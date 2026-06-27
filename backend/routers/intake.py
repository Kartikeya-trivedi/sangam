"""Report intake — POST /report/lost and /report/found (voice or text + optional photo)."""
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from constants import CENTRE_SLUGS, slugify_centre
from models import ReportResponse
from services import intake

router = APIRouter(prefix="/api/v1/report", tags=["intake"])

# Spoken errors are returned in the reporter's language so the frontend can TTS them directly.
_SPOKEN = {
    "centre_required": "कृपया केंद्र का नाम बताएं।",
    "no_input": "कृपया बोलकर या लिखकर जानकारी दें।",
    "consent_required": "क्या हम आपकी जानकारी ढूंढने के लिए इस्तेमाल कर सकते हैं? कृपया 'हाँ' दबाएं।",
}


def _save_upload(upload: UploadFile | None, suffix: str) -> str | None:
    if upload is None:
        return None
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(upload.file.read())
    return path


async def _handle(role: str, *, text, audio, photo, language_hint, centre_id,
                  consent_given, reporter_mobile, reporter_name,
                  gender, age_band, last_seen_location, top_k) -> JSONResponse:
    if not centre_id:
        return JSONResponse(status_code=400,
                            content={"error": "centre_required", "spoken": _SPOKEN["centre_required"]})
    centre = slugify_centre(centre_id)
    if centre not in CENTRE_SLUGS:
        return JSONResponse(status_code=400,
                            content={"error": "unknown_centre", "spoken": _SPOKEN["centre_required"]})
    if not consent_given:
        return JSONResponse(status_code=403,
                            content={"error": "consent_required", "spoken": _SPOKEN["consent_required"]})
    audio_path = _save_upload(audio, ".webm")
    photo_path = _save_upload(photo, ".jpg")
    try:
        has_taps = any((gender, age_band, last_seen_location))
        if not (text and text.strip()) and audio_path is None and photo_path is None and not has_taps:
            return JSONResponse(status_code=400,
                                content={"error": "no_input", "spoken": _SPOKEN["no_input"]})
        result: ReportResponse = intake.process_report(
            role, text=text, audio_path=audio_path, photo_path=photo_path,
            language_hint=language_hint, centre_id=centre, consent_given=consent_given,
            reporter_mobile=reporter_mobile, reporter_name=reporter_name,
            gender=gender, age_band=age_band, last_seen_location=last_seen_location, top_k=top_k,
        )
        return JSONResponse(content=result.model_dump(mode="json"))
    finally:
        for p in (audio_path, photo_path):
            if p and os.path.exists(p):
                os.remove(p)


@router.post("/lost")
async def report_lost(
    centre_id: str = Form(...),
    text: str | None = Form(None),
    language_hint: str | None = Form(None),
    consent_given: bool = Form(True),
    reporter_mobile: str | None = Form(None),
    reporter_name: str | None = Form(None),
    gender: str | None = Form(None),
    age_band: str | None = Form(None),
    last_seen_location: str | None = Form(None),
    top_k: int = Form(5),
    audio: UploadFile | None = File(None),
    photo: UploadFile | None = File(None),
):
    return await _handle("lost", text=text, audio=audio, photo=photo, language_hint=language_hint,
                         centre_id=centre_id, consent_given=consent_given,
                         reporter_mobile=reporter_mobile, reporter_name=reporter_name,
                         gender=gender, age_band=age_band, last_seen_location=last_seen_location,
                         top_k=top_k)


@router.post("/found")
async def report_found(
    centre_id: str = Form(...),
    text: str | None = Form(None),
    language_hint: str | None = Form(None),
    consent_given: bool = Form(True),
    reporter_mobile: str | None = Form(None),
    reporter_name: str | None = Form(None),
    gender: str | None = Form(None),
    age_band: str | None = Form(None),
    last_seen_location: str | None = Form(None),
    top_k: int = Form(5),
    audio: UploadFile | None = File(None),
    photo: UploadFile | None = File(None),
):
    return await _handle("found", text=text, audio=audio, photo=photo, language_hint=language_hint,
                         centre_id=centre_id, consent_given=consent_given,
                         reporter_mobile=reporter_mobile, reporter_name=reporter_name,
                         gender=gender, age_band=age_band, last_seen_location=last_seen_location,
                         top_k=top_k)
