"""Sarvam speech — Saaras STT + Bulbul TTS — with offline fallbacks.

Speech is optional (`pip install -e '.[speech]'`). Without the `sarvamai` package or a
SARVAM_API_KEY, STT returns an empty transcript (the router then asks for typed input) and TTS
returns None (the frontend falls back to the browser's Web Speech API). The app never crashes
because speech is unavailable — that is the camp-resilience contract.
"""
from __future__ import annotations

from config import settings

try:
    from sarvamai import SarvamAI  # type: ignore
except Exception:
    SarvamAI = None

_client = None


def available() -> bool:
    return bool(settings.has_sarvam and SarvamAI is not None)


def _get_client():
    global _client
    if not available():
        return None
    if _client is None:
        _client = SarvamAI(api_subscription_key=settings.sarvam_api_key)
    return _client


def transcribe(audio_path: str, language_hint: str | None = None) -> tuple[str, str]:
    """(transcript, detected_language). ('', 'unknown') signals STT-unavailable -> use text input."""
    client = _get_client()
    if client is None:
        return "", "unknown"
    try:
        with open(audio_path, "rb") as f:
            # saarika = transcription (native script); 'saaras' is the translate model (wrong here,
            # and 400s on this account). v2.5 verified live. Claude does any translation (§8).
            resp = client.speech_to_text.transcribe(
                file=f, model="saarika:v2.5", language_code=language_hint or "unknown"
            )
        return (getattr(resp, "transcript", "") or "",
                getattr(resp, "language_code", None) or language_hint or "unknown")
    except Exception:
        return "", "unknown"


def synthesize(text: str, language: str = "hi") -> bytes | None:
    """Native-script text -> audio bytes (Bulbul). None -> frontend uses Web Speech API."""
    client = _get_client()
    if client is None or not text.strip():
        return None
    try:
        resp = client.text_to_speech.convert(text=text, target_language_code=language,
                                              model="bulbul:v2")
        audios = getattr(resp, "audios", None)
        if audios:
            import base64
            return base64.b64decode(audios[0])
        return None
    except Exception:
        return None
