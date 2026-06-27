"""Announcements + generic TTS (spec §7, §12). Minor announcements are BLOCKED (§12.1)."""
from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException

from db import faiss_index
from models import AnnounceRequest, AnnounceResponse, SpeakRequest, SpeakResponse
from safety import audit, create_staff_alert, is_minor
from services import claude, speech

router = APIRouter()


def _audio_data_url(audio: bytes | None) -> str | None:
    """Inline TTS audio as a data: URL so the scaffold needs no object storage."""
    if not audio:
        return None
    return "data:audio/wav;base64," + base64.b64encode(audio).decode("ascii")


@router.post("/announce", response_model=AnnounceResponse)
def announce(req: AnnounceRequest):
    person = faiss_index.get_person(req.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="person_not_found")

    # §12.1 — minors are never broadcast publicly. Alert staff privately + open verification.
    if is_minor(person):
        create_staff_alert(person, person.centre_id)
        audit("system", "announce_blocked_minor", person.id)
        return AnnounceResponse(announcement_text="", blocked=True, staff_alert_created=True)

    text = claude.draft_announcement(person, req.target_language)
    audio = None
    try:
        audio = speech.synthesize(text, req.target_language)
    except NotImplementedError:
        pass  # Bulbul not wired yet
    audit("staff", "announce", person.id, language=req.target_language)
    # TODO: also push a reunification event to the ops dashboard (websocket / poll).
    return AnnounceResponse(announcement_text=text, audio_url=_audio_data_url(audio))


@router.post("/speak", response_model=SpeakResponse)
def speak(req: SpeakRequest):
    """Generic TTS for UI guidance (§7). Returns null audio_url when Bulbul isn't wired —
    the pilgrim app then falls back to the browser's built-in speech synthesis (§2.2)."""
    audio = None
    try:
        audio = speech.synthesize(req.text, req.language)
    except NotImplementedError:
        pass
    return SpeakResponse(audio_url=_audio_data_url(audio))
