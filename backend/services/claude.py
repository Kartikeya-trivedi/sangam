"""Claude — the reasoning core (spec §4, §8).

One reused extraction prompt (strict JSON), one re-rank prompt, one announcement prompt.
Claude is the CROSS-LANGUAGE BRIDGE: native-script transcript in -> structured English
Person + native-language readback summary out. Matching then runs on the English fields,
so a Tamil report matches a Marathi found-log automatically (§8).

When ANTHROPIC_API_KEY is absent, this module falls back to a naive keyword-based mock so
the whole pipeline still runs offline for the demo. The mock is clearly marked — replace
with the real call in Phase 1. NEVER set ANTHROPIC_API_KEY in the Claude Code shell (§14).
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone

from config import settings
from models import MatchResult, Person

try:
    from anthropic import Anthropic  # type: ignore
except Exception:
    Anthropic = None

_client = None


def _get_client():
    global _client
    if not settings.has_anthropic or Anthropic is None:
        return None
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


EXTRACTION_SYSTEM = """You convert a missing-person report (in any Indian language,
possibly code-mixed, misspelled, or vague) into a STRICT JSON object.
Translate-understand the input, then emit canonical ENGLISH attribute values
(e.g. clothing ["blue kurta"], languages_spoken ["tamil"]) PLUS a `native_summary`
written back in the reporter's own language and script, for spoken readback.
Return ONLY the JSON object — no preamble, no code fences.
Keys: age_band(child|teen|adult|elderly|unknown), gender(male|female|other|unknown),
clothing[], distinguishing[], height_band(short|medium|tall|unknown), languages_spoken[],
last_seen_location, last_seen_time, native_summary, is_minor(bool)."""


def _ttl() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.ttl_days)


def extract_profile(transcript: str, role: str, spoken_language: str = "unknown") -> Person:
    """Native-script transcript -> canonical English Person (+ native_summary)."""
    client = _get_client()
    if client is None:
        data = _mock_extract(transcript)
    else:
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": transcript or ""}],
        )
        data = _parse_json(msg.content[0].text)

    is_minor = bool(data.get("is_minor")) or data.get("age_band") in ("child", "teen")
    return Person(
        id=str(uuid.uuid4()),
        role=role,  # type: ignore[arg-type]
        age_band=data.get("age_band", "unknown"),
        gender=data.get("gender", "unknown"),
        clothing=data.get("clothing", []) or [],
        distinguishing=data.get("distinguishing", []) or [],
        height_band=data.get("height_band", "unknown"),
        languages_spoken=data.get("languages_spoken", []) or [],
        last_seen_location=data.get("last_seen_location"),
        last_seen_time=data.get("last_seen_time"),
        spoken_language=spoken_language,
        raw_transcript=transcript or "",
        native_summary=data.get("native_summary") or (transcript or "")[:140],
        is_minor=is_minor,
        created_at=datetime.now(timezone.utc),
        ttl_expires_at=_ttl(),
    )


def rerank_candidates(query: Person, candidates: list[MatchResult]) -> list[MatchResult]:
    """Claude re-ranks the top ~10 and writes a one-line 'why it matched' per candidate (§9)."""
    if not candidates:
        return candidates
    client = _get_client()
    if client is None:
        for c in candidates:
            c.explanation = _mock_explanation(query, c)
        return candidates
    # TODO (Phase 1): send query + candidate summaries; ask Claude for a reordered list of
    # ids plus a one-line native/English explanation each. Apply order + explanations here.
    for c in candidates:
        c.explanation = _mock_explanation(query, c)
    return candidates


def draft_announcement(person: Person, target_language: str) -> str:
    """Announcement text in the TARGET language's native script (handed to Bulbul, §8)."""
    client = _get_client()
    if client is None:
        return person.native_summary or "कृपया लापता व्यक्ति के परिजन सूचना केंद्र पर संपर्क करें।"
    # TODO (Phase 1): real Claude call producing native-script announcement text.
    return person.native_summary


# --- naive offline fallbacks (DEMO ONLY; replace with Claude) -----------------------------
_COLORS = ["blue", "red", "white", "green", "yellow", "black", "orange", "saffron"]
_GARMENTS = {"kurta": "kurta", "saree": "saree", "sari": "saree", "dhoti": "dhoti", "shirt": "shirt", "salwar": "salwar"}
_LANGS = ["tamil", "hindi", "marathi", "telugu", "bengali", "gujarati", "kannada", "malayalam", "punjabi"]


def _mock_extract(text: str) -> dict:
    t = (text or "").lower()
    age = (
        "elderly" if any(w in t for w in ["elder", "old", "buzurg", "bujurg"])
        else "child" if any(w in t for w in ["child", "bachcha", "kid", "boy", "girl"])
        else "unknown"
    )
    gender = (
        "male" if any(w in t for w in ["man", "male", "aadmi", "boy", "father", "uncle"])
        else "female" if any(w in t for w in ["woman", "female", "aurat", "girl", "mother", "aunty"])
        else "unknown"
    )
    color = next((c for c in _COLORS if c in t), None)
    garment = next((v for k, v in _GARMENTS.items() if k in t), None)
    clothing = [" ".join(x for x in [color, garment] if x)] if garment else []
    langs = [l for l in _LANGS if l in t]
    return {
        "age_band": age,
        "gender": gender,
        "clothing": clothing,
        "distinguishing": [],
        "height_band": "unknown",
        "languages_spoken": langs,
        "last_seen_location": None,
        "last_seen_time": None,
        "native_summary": (text or "").strip()[:140],
        "is_minor": age in ("child", "teen"),
    }


def _mock_explanation(q: Person, c: MatchResult) -> str:
    bits = []
    if c.face_score and c.face_score > 0.5:
        bits.append("strong face match")
    if c.attr_score and c.attr_score > 0.4:
        bits.append("matching description")
    if c.geo_score and c.geo_score >= 0.6:
        bits.append("nearby location")
    return f"{', '.join(bits) or 'possible match'} (score {c.score:.2f})"


def _parse_json(text: str) -> dict:
    """Defensive parse: strip code fences, grab the first JSON object (§8 prompt note)."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(m.group(0)) if m else {}
