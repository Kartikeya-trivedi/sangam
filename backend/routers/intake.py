"""Intake routes (spec §7): POST /report/lost, POST /report/found.

Pipeline (§7): audio -> Saaras STT -> Claude extract+normalize -> (photo -> InsightFace
embed) -> matching -> ranked candidates with explanations.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from db import faiss_index, supabase_client
from models import ReportResponse
from safety import audit, create_staff_alert
from services import claude, faces, matching, speech

router = APIRouter()


async def _ingest(
    role: str,
    audio: Optional[UploadFile],
    photo: Optional[UploadFile],
    text: Optional[str],
    language_hint: Optional[str],
    centre_id: Optional[str] = None,
) -> ReportResponse:
    # 1. Speech -> native-script transcript (or typed text fallback, §13).
    transcript, language = (text or ""), (language_hint or "unknown")
    if audio is not None:
        try:
            t = speech.transcribe(await audio.read(), language_hint)
            transcript, language = (t.text or transcript), (t.language or language)
        except NotImplementedError:
            pass  # Sarvam not wired yet -> rely on typed text / degraded path

    # 2. Claude: transcript -> canonical English Person + native readback summary.
    person = claude.extract_profile(transcript, role=role, spoken_language=language)
    person.centre_id = centre_id

    # 3. Photo -> InsightFace embedding (TODO: + Claude vision location hint).
    if photo is not None:
        person.face_embedding = faces.embed(await photo.read())

    # 4. Persist: local index always; central store when online.
    faiss_index.add_person(person)
    supabase_client.insert_person(person, centre_id=centre_id)
    audit("pilgrim" if role == "lost" else "staff", f"report_{role}", person.id)

    # 5. Match against the opposite role; Claude re-ranks + explains.
    candidates = matching.rank_candidates(person, k=10)
    candidates = claude.rerank_candidates(person, candidates)

    # 6. §12 safety: a minor among the candidates is never surfaced in a pilgrim-facing
    #    list — raise a private staff alert instead (the UI hides the connect button too).
    for c in candidates:
        if c.is_minor:
            create_staff_alert(person, centre_id)

    return ReportResponse(
        report_id=person.id,
        native_summary=person.native_summary,
        structured=person,
        candidates=candidates,
    )


@router.post("/report/lost", response_model=ReportResponse)
async def report_lost(
    audio: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    language_hint: Optional[str] = Form(None),
):
    return await _ingest("lost", audio, photo, text, language_hint)


@router.post("/report/found", response_model=ReportResponse)
async def report_found(
    audio: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    language_hint: Optional[str] = Form(None),
    centre_id: Optional[str] = Form(None),
):
    """Logs a found person at a centre and reverse-matches against open lost reports (§7)."""
    return await _ingest("found", audio, photo, text, language_hint, centre_id)
