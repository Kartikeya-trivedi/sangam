"""Announcements (TTS) + UI speech. Minors are never publicly announced (safety §)."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

import safety
from db import repo
from models import AnnounceRequest, SpeakRequest
from services import claude, speech

router = APIRouter(prefix="/api/v1", tags=["announce"])

_AUDIO_DIR = Path(__file__).resolve().parents[1] / ".audio_cache"
_AUDIO_DIR.mkdir(exist_ok=True)


def _write_audio(audio: bytes | None) -> str | None:
    if not audio:
        return None
    key = f"{uuid.uuid4()}.wav"
    (_AUDIO_DIR / key).write_bytes(audio)
    return f"/api/v1/speak/audio/{key}"


@router.post("/announce")
def announce(req: AnnounceRequest):
    person = repo.get_person(req.person_id)
    if not person:
        return JSONResponse(status_code=404, content={"error": "person_not_found"})

    allowed, reason = safety.can_announce(person)
    if not allowed:
        repo.insert_announcement(person.id, req.target_language, "", triggered_by=req.triggered_by,
                                 is_minor_blocked=True)
        repo.write_audit(req.triggered_by, "announcement_triggered", person_id=person.id,
                         meta={"is_minor_blocked": True})
        return JSONResponse(status_code=403, content={
            "error": reason,
            "spoken": "नाबालिग की जानकारी सार्वजनिक नहीं की जा सकती। कृपया स्टाफ से संपर्क करें।",
            "action_required": "guardian_verification"})

    text = claude.draft_announcement(person, req.target_language)
    audio_url = _write_audio(speech.synthesize(text, req.target_language))
    repo.insert_announcement(person.id, req.target_language, text, triggered_by=req.triggered_by,
                             is_minor_blocked=False, audio_storage_key=audio_url)
    repo.write_audit(req.triggered_by, "announcement_triggered", person_id=person.id,
                     meta={"is_minor_blocked": False})
    return {"announcement_text": text, "audio_url": audio_url, "blocked": False,
            "staff_alert_created": False}


@router.post("/speak")
def speak(req: SpeakRequest):
    """TTS for UI guidance strings (ephemeral)."""
    audio_url = _write_audio(speech.synthesize(req.text, req.language))
    return {"audio_url": audio_url}


@router.get("/speak/audio/{key}")
def speak_audio(key: str):
    path = _AUDIO_DIR / Path(key).name  # basename guards against path traversal
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": "audio_not_found"})
    return FileResponse(path, media_type="audio/wav")
