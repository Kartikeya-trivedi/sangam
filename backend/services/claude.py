"""Claude — the reasoning + cross-language normalization core.

Claude turns a messy, multilingual, possibly-vague report into a canonical-English Person
profile plus a `native_summary` in the reporter's own language. It also re-ranks the top
matches with a human explanation, and drafts public announcements.

Three design rules (from CLAUDE.md + the data analysis):
  1. GRACEFUL DEGRADATION — with no ANTHROPIC_API_KEY (or any API error) every function falls
     back to a deterministic rule-based path so the whole pipeline still runs offline. NEVER
     crash the request because Claude is unavailable.
  2. STRUCTURED OUTPUT — extraction uses output_config.format (json_schema) so we get valid
     JSON without brittle string-parsing. We still parse defensively as a backstop.
  3. CANONICAL ENGLISH for matching fields; native script only in native_summary / announcements.

Model + API usage follow the current Claude API (Opus 4.8): adaptive-thinking-only family, no
temperature/top_p, structured outputs via output_config.format.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone

from config import settings
from constants import AGE_BANDS, is_minor_band, slugify_centre
from models import MatchResult, Person

try:
    import anthropic
except Exception:  # pragma: no cover - anthropic always installed in this project
    anthropic = None

_client = None


def _get_client():
    global _client
    if not settings.has_anthropic or anthropic is None:
        return None
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


# --- extraction --------------------------------------------------------------------------
EXTRACTION_SYSTEM = """You are a data-extraction service for a missing-persons reunification \
system at the Nashik-Trimbakeshwar Kumbh Mela. You receive a report transcript in any Indian \
language (possibly code-mixed, misspelled, or vague) describing a missing person. Extract \
canonical, English-normalized attributes.

Rules:
- Never fabricate. If something is not stated, use null (strings) or [] (lists).
- Normalize to canonical English: "नीली कुर्ता" -> clothing ["blue kurta"]; languages lowercase.
- Map age words to a band: child/बच्चा -> "0-12"; teen/किशोर -> "13-17"; young adult -> "18-40"; \
middle-aged/अधेड़ -> "41-60"; older -> "61-70"; elderly/बुज़ुर्ग/दादाजी -> "71-80"; very old -> "80+". \
If unclear, use "unknown".
- clothing: colour + garment, e.g. ["blue kurta", "white dhoti", "red saree"].
- distinguishing_features: ["walking stick", "hearing aid", "scar on forehead", "limp"].
- languages_spoken: the language the MISSING person speaks (not the reporter).
- last_seen_location: a recognizable Kumbh landmark name if mentioned, else null.
- name: the missing person's name if stated (strip honorifics like Shri/Smt), else null.
- native_summary: ONE short sentence in the REPORTER's own language and script, for spoken readback."""

_EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "age_band": {"type": "string", "enum": [*AGE_BANDS, "unknown"]},
        "gender": {"type": "string", "enum": ["male", "female", "unknown"]},
        "name": {"type": ["string", "null"]},
        "clothing": {"type": "array", "items": {"type": "string"}},
        "distinguishing_features": {"type": "array", "items": {"type": "string"}},
        "height_band": {"type": "string", "enum": ["short", "medium", "tall", "unknown"]},
        "languages_spoken": {"type": "array", "items": {"type": "string"}},
        "last_seen_location": {"type": ["string", "null"]},
        "native_summary": {"type": "string"},
    },
    "required": [
        "age_band", "gender", "name", "clothing", "distinguishing_features",
        "height_band", "languages_spoken", "last_seen_location", "native_summary",
    ],
}


def extract_profile(transcript: str, role: str, centre_id: str,
                    spoken_language: str = "unknown") -> Person:
    """Native-script transcript -> canonical-English Person (+ native_summary)."""
    data = _extract_fields(transcript)
    age_band = data.get("age_band") or "unknown"
    return Person(
        id=str(uuid.uuid4()),
        role=role,  # type: ignore[arg-type]
        age_band=age_band,  # type: ignore[arg-type]
        gender=data.get("gender") or "unknown",  # type: ignore[arg-type]
        name=(data.get("name") or None),
        clothing=data.get("clothing") or [],
        distinguishing_features=data.get("distinguishing_features") or [],
        height_band=data.get("height_band") or "unknown",  # type: ignore[arg-type]
        languages_spoken=data.get("languages_spoken") or [],
        last_seen_location=data.get("last_seen_location") or None,
        spoken_language=spoken_language,
        raw_transcript=transcript or "",
        native_summary=data.get("native_summary") or (transcript or "")[:140],
        is_minor=is_minor_band(age_band),
        centre_id=slugify_centre(centre_id),
        created_at=datetime.now(timezone.utc),
    )


def _extract_fields(transcript: str) -> dict:
    client = _get_client()
    if client is None or not (transcript or "").strip():
        return _mock_extract(transcript)
    try:
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=EXTRACTION_SYSTEM,
            output_config={"effort": "low",
                           "format": {"type": "json_schema", "schema": _EXTRACTION_SCHEMA}},
            messages=[{"role": "user", "content": transcript}],
        )
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        return _parse_json(text) or _mock_extract(transcript)
    except Exception:
        # Any API/SDK error -> degrade to the rule-based path for this one request.
        return _mock_extract(transcript)


# --- re-rank -----------------------------------------------------------------------------
_RERANK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ranking": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "candidate_id": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "explanation": {"type": "string"},
                },
                "required": ["candidate_id", "confidence", "explanation"],
            },
        }
    },
    "required": ["ranking"],
}

RERANK_SYSTEM = """You re-rank candidate matches for a missing-persons reunification system. \
Descriptions may be vague or written from different perspectives (a worried family vs a calm \
volunteer). Judge whether each candidate is plausibly the SAME person.
Rules: if gender clearly differs, confidence is "low". Age bands off by one are still plausible \
(estimates vary). Missing name/phone does not lower confidence by itself. Write each explanation \
in one plain sentence a volunteer can act on. Return ALL candidates, most likely first."""


def rerank_candidates(query: Person, candidates: list[MatchResult]) -> list[MatchResult]:
    """Claude re-orders the top candidates and writes a one-line explanation for each."""
    if not candidates:
        return candidates
    client = _get_client()
    if client is None:
        for c in candidates:
            c.explanation = _heuristic_explanation(c)
        return candidates
    try:
        payload = {
            "query": _person_brief(query),
            "candidates": [{"candidate_id": c.candidate_id, **_match_brief(c)} for c in candidates],
        }
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=RERANK_SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": _RERANK_SCHEMA}},
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        ranking = (_parse_json(text) or {}).get("ranking", [])
        by_id = {c.candidate_id: c for c in candidates}
        ordered: list[MatchResult] = []
        for item in ranking:
            c = by_id.pop(item.get("candidate_id", ""), None)
            if c:
                c.explanation = item.get("explanation") or _heuristic_explanation(c)
                c.confidence = item.get("confidence") or c.confidence  # type: ignore[assignment]
                ordered.append(c)
        ordered.extend(by_id.values())  # any not mentioned keep their score order
        return ordered or candidates
    except Exception:
        for c in candidates:
            c.explanation = _heuristic_explanation(c)
        return candidates


# --- announcement ------------------------------------------------------------------------
ANNOUNCE_SYSTEM = """Draft a short, calm loudspeaker announcement for a FOUND person at a Kumbh \
Mela help desk, in the requested language and its native script. Include approximate age, gender, \
clothing, distinguishing features, and which centre they are at. NEVER include the person's name \
or any personal identifier, and never use the word "missing". 2-3 simple sentences for elderly / \
low-literacy listeners. Return ONLY the announcement text."""


def draft_announcement(person: Person, target_language: str) -> str:
    client = _get_client()
    if client is None:
        return _template_announcement(person)
    try:
        details = {
            "age_band": person.age_band, "gender": person.gender,
            "clothing": person.clothing, "distinguishing_features": person.distinguishing_features,
            "centre_id": person.centre_id, "languages_spoken": person.languages_spoken,
            "target_language": target_language,
        }
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=512,
            system=ANNOUNCE_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(details, ensure_ascii=False)}],
        )
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        return text.strip() or _template_announcement(person)
    except Exception:
        return _template_announcement(person)


# --- briefs for prompts ------------------------------------------------------------------
def _person_brief(p: Person) -> dict:
    return {"age_band": p.age_band, "gender": p.gender, "name": p.name,
            "clothing": p.clothing, "distinguishing_features": p.distinguishing_features,
            "languages_spoken": p.languages_spoken, "last_seen_location": p.last_seen_location}


def _match_brief(c: MatchResult) -> dict:
    b = c.breakdown
    return {"summary": c.candidate_summary, "score": c.final_score,
            "signals": {k: v for k, v in b.model_dump().items() if v is not None}}


# --- rule-based fallbacks (deterministic; used when Claude is unavailable) ----------------
_COLORS = ["blue", "red", "white", "green", "yellow", "black", "orange", "saffron", "pink"]
_GARMENTS = {"kurta": "kurta", "saree": "saree", "sari": "saree", "dhoti": "dhoti",
             "shirt": "shirt", "salwar": "salwar", "frock": "frock", "uniform": "uniform"}
_LANGS = ["tamil", "hindi", "marathi", "telugu", "bengali", "gujarati", "kannada",
          "malayalam", "punjabi", "urdu", "bhojpuri", "maithili", "awadhi", "odia", "assamese"]


def _mock_extract(text: str) -> dict:
    t = (text or "").lower()
    if any(w in t for w in ["child", "bachcha", "बच्चा", "kid", "boy", "girl", "लड़का", "लड़की"]):
        age = "0-12"
    elif any(w in t for w in ["teen", "किशोर"]):
        age = "13-17"
    elif any(w in t for w in ["very old", "80", "अति वृद्ध"]):
        age = "80+"
    elif any(w in t for w in ["elder", "old", "buzurg", "बुज़ुर्ग", "वृद्ध", "dada", "दादा", "nana"]):
        age = "71-80"
    elif any(w in t for w in ["middle", "अधेड़"]):
        age = "41-60"
    else:
        age = "unknown"
    gender = (
        "male" if any(w in t for w in ["man", "male", "aadmi", "आदमी", "boy", "father", "dada", "uncle"])
        else "female" if any(w in t for w in ["woman", "female", "aurat", "औरत", "girl", "mother", "aunty", "widow"])
        else "unknown"
    )
    color = next((c for c in _COLORS if c in t), None)
    garment = next((v for k, v in _GARMENTS.items() if k in t), None)
    clothing = [" ".join(x for x in [color, garment] if x)] if garment else []
    langs = [lang for lang in _LANGS if lang in t]
    return {
        "age_band": age, "gender": gender, "name": None, "clothing": clothing,
        "distinguishing_features": [], "height_band": "unknown", "languages_spoken": langs,
        "last_seen_location": None,
        "native_summary": (text or "").strip()[:140],
    }


def _heuristic_explanation(c: MatchResult) -> str:
    b, bits = c.breakdown, []
    if b.face and b.face > 0.5:
        bits.append("strong face match")
    if b.name and b.name > 0.7:
        bits.append("matching name")
    if b.age == 1.0:
        bits.append("same age band")
    if b.gender == 1.0:
        bits.append("same gender")
    if b.language == 1.0:
        bits.append("shared language")
    if b.location and b.location >= 0.75:
        bits.append("nearby last-seen location")
    return f"{', '.join(bits) or 'partial attribute overlap'} (score {c.final_score:.2f})"


def _template_announcement(p: Person) -> str:
    desc = ", ".join(p.clothing[:2]) or "unidentified clothing"
    age = p.age_band if p.age_band != "unknown" else "adult"
    return (f"Attention please. {age} {p.gender if p.gender != 'unknown' else 'person'}, "
            f"wearing {desc}, is safe at the {p.centre_id.replace('_', ' ')} help desk. "
            f"Family members may collect them there.")


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        try:
            return json.loads(m.group(0)) if m else {}
        except Exception:
            return {}
