"""Sarvam speech wrappers (spec §14). Speech ONLY — translation is Claude's job (§8).

Saaras    -> STT, auto-detects the Indian language, returns native-script transcript.
Bulbul v3 -> TTS, needs NATIVE-SCRIPT text + target_language_code, returns audio.

Both degrade gracefully when the key is missing or the service is unreachable so the
camp kiosk never goes fully down (§13). Callers fall back to typed input / browser TTS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from config import settings

try:
    from sarvamai import SarvamAI  # type: ignore
except Exception:
    SarvamAI = None

_client = None


def _get_client():
    global _client
    if not settings.has_sarvam or SarvamAI is None:
        return None
    if _client is None:
        _client = SarvamAI(api_subscription_key=settings.sarvam_api_key)
    return _client


@dataclass
class Transcript:
    text: str       # native-script transcript ("" when unavailable)
    language: str   # detected language code, e.g. "ta-IN"


def transcribe(audio_bytes: bytes, language_hint: Optional[str] = None) -> Transcript:
    """Saaras STT. Returns native-script text + detected language."""
    client = _get_client()
    if client is None:
        # Offline/degraded: caller should fall back to typed input (§13).
        return Transcript(text="", language=language_hint or "unknown")
    # TODO (Phase 1): wire Sarvam Saaras.
    #   resp = client.speech_to_text.transcribe(file=audio_bytes, model="saaras:v2")
    #   return Transcript(text=resp.transcript, language=resp.language_code)
    raise NotImplementedError("Wire Sarvam Saaras STT here")


def synthesize(text: str, language: str) -> Optional[bytes]:
    """Bulbul v3 TTS. `text` MUST be native script (never romanized). Returns audio bytes."""
    client = _get_client()
    if client is None:
        return None
    # TODO (Phase 1): wire Sarvam Bulbul v3.
    #   resp = client.text_to_speech.convert(text=text, target_language_code=language,
    #                                         model="bulbul:v3", speaker="...")
    #   return base64.b64decode(resp.audios[0])
    raise NotImplementedError("Wire Sarvam Bulbul v3 TTS here")
