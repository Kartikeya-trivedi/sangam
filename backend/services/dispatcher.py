"""Sahayak — the agentic reunification dispatcher.

Given an open LOST report, Sahayak works the case the way a control-room officer would, but in
seconds and in every language. It (1) reads the report, (2) scans every centre for matches,
(3) PREDICTS where the person likely drifted using the real Kumbh crowd geography, (4) dispatches
the right action — a reunification announcement when there's a strong found-match, otherwise a
staff BOLO to the predicted-zone help desks (and NEVER a public announcement for a minor — that
becomes a private staff alert, child-safety §12) — and (5) recommends the next step.

It yields each step as soon as it's computed, so the dashboard can show Claude reasoning live.
Everything degrades gracefully with no keys (heuristic drift + template announcement).
"""
from __future__ import annotations

import base64
import json
from collections.abc import Iterator

from config import settings
from db import repo
from models import Person
from services import claude, geo, matching, speech


def _step(n: int, kind: str, title: str, detail: str, data: dict | None = None,
          status: str = "done") -> dict:
    return {"n": n, "kind": kind, "title": title, "detail": detail,
            "status": status, "data": data or {}}


def _origin(person: Person) -> tuple[float, float]:
    return (geo.location_to_coords(person.last_seen_location)
            or geo.CENTRE_COORDS.get(person.centre_id)
            or (19.9975, 73.7898))


def _nearby(lat: float, lng: float, limit: int = 8) -> list[dict]:
    """Real points around the last-seen location, nearest first (grounds the drift reasoning)."""
    pts: list[dict] = []
    for name, (la, lo) in geo.LANDMARKS.items():
        pts.append({"name": name.title(), "lat": la, "lng": lo, "type": "landmark"})
    for slug, (la, lo) in geo.CENTRE_COORDS.items():
        pts.append({"name": slug.replace("_", " ").title(), "lat": la, "lng": lo, "type": "help_desk"})
    for c in geo.chokepoints():
        pts.append({"name": c["location_name"], "lat": c["lat"], "lng": c["lng"],
                    "type": "chokepoint", "category": c.get("category")})
    for p in pts:
        p["km"] = round(geo.haversine_km(lat, lng, p["lat"], p["lng"]), 2)
    pts.sort(key=lambda p: p["km"])
    return pts[:limit]


# --- drift prediction (Claude over real crowd geography) ----------------------------------
_DRIFT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "zones": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "lat": {"type": "number"}, "lng": {"type": "number"},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "reason": {"type": "string"},
            },
            "required": ["name", "lat", "lng", "priority", "reason"],
        }},
        "rationale": {"type": "string"},
    },
    "required": ["zones", "rationale"],
}

_DRIFT_SYSTEM = """You are Sahayak, a reunification dispatcher at the Nashik-Trimbakeshwar Kumbh \
Mela. A person was last seen at a location during the snan (ritual bathing), when dense crowds \
flow predictably toward the ghats and bottleneck at chokepoints. Given the last-seen point and \
nearby landmarks / help desks / chokepoints (each with a distance in km), predict the 2-3 ZONES \
the person most likely drifted to and where to send help-desk staff FIRST. Choose each zone's \
lat/lng from the provided candidate points (do not invent coordinates). Elderly and children \
move slowly and get pushed toward bottlenecks. Give one short, concrete reason per zone grounded \
in crowd flow. Also give a one-sentence overall rationale."""


def _heuristic_zones(nearby: list[dict]) -> dict:
    zs = [{"name": p["name"], "lat": p["lat"], "lng": p["lng"],
           "priority": "high" if i == 0 else "medium",
           "reason": f"{p['km']} km away ({p['type'].replace('_', ' ')}) — nearest reachable point"}
          for i, p in enumerate(nearby[:3])]
    return {"zones": zs, "rationale": "Nearest reachable points to the last-seen location."}


def _predict_zones(person: Person, origin: tuple[float, float], nearby: list[dict]) -> dict:
    client = claude._get_client()
    if client is None or not nearby:
        return _heuristic_zones(nearby)
    payload = {"last_seen": person.last_seen_location, "age_band": person.age_band,
               "origin": {"lat": origin[0], "lng": origin[1]}, "candidate_points": nearby}
    try:
        msg = client.messages.create(
            model=settings.anthropic_model, max_tokens=900, system=_DRIFT_SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": _DRIFT_SCHEMA}},
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        out = claude._parse_json(text)
        return out if out.get("zones") else _heuristic_zones(nearby)
    except Exception:
        return _heuristic_zones(nearby)


# --- dispatch (adaptive: reunification announce vs staff BOLO; minor-safe) ------------------
def _audio_url(audio: bytes | None) -> str | None:
    if not audio:
        return None
    return "data:audio/wav;base64," + base64.b64encode(audio).decode("ascii")


def _dispatch(person: Person, zones: list[dict], cands: list) -> dict:
    zone_names = [z.get("name") for z in zones][:3]
    lang = person.spoken_language if person.spoken_language not in (None, "", "unknown") else "hi"

    if person.is_minor:
        return {"action": "staff_alert", "blocked": True, "language": None, "zones": zone_names,
                "text": ("Minor — no public announcement (child-safety §12). Private staff alert "
                         "created; guardian verification required before any reunion."),
                "audio_url": None}

    top = cands[0] if cands else None
    if top and top.final_score >= settings.high_confidence_threshold:
        found = repo.get_person(top.candidate_id)
        if found is not None and not found.is_minor:
            text = claude.draft_announcement(found, lang)
            return {"action": "reunification_announce", "blocked": False, "language": lang,
                    "zones": [found.centre_id.replace("_", " ").title()], "found_id": found.id,
                    "text": text, "audio_url": _audio_url(speech.synthesize(text, lang))}

    near = zone_names[0] if zone_names else "the nearest ghat"
    text = (f"Staff alert: look out for {person.summary()}. Likely drifting toward {near}. "
            f"If seen, guide them to the nearest Kho-Ya-Paya help desk and log them as found.")
    return {"action": "staff_bolo", "blocked": False, "language": "en", "zones": zone_names,
            "text": text, "audio_url": None}


def _verdict(person: Person, cands: list) -> dict:
    if not cands:
        return {"confidence": "searching", "title": "No confident match yet",
                "detail": ("Announcements dispatched to the predicted zones. Sahayak will "
                           "re-check this case against every new found-report automatically."),
                "notify_family": False, "mobile": person.reporter_mobile}
    top = cands[0]
    strong = top.final_score >= settings.high_confidence_threshold
    pct = round(top.final_score * 100)
    return {
        "confidence": top.confidence,
        "title": f"{'Strong' if strong else 'Possible'} match — {pct}%",
        "detail": (f"Recommend {'notifying the family and requesting visual confirmation' if strong else 'staff review before contacting family'}. "
                   f"{top.explanation}"),
        "notify_family": strong, "candidate_id": top.candidate_id, "mobile": person.reporter_mobile,
    }


def run(report_id: str, language: str | None = None) -> Iterator[dict]:
    """Yield Sahayak's reasoning steps for a case, one at a time, as each completes."""
    person = repo.get_person(report_id)
    if person is None:
        yield _step(0, "error", "Case not found", report_id, status="error")
        return

    origin = _origin(person)
    yield _step(1, "assess", "Reading the report",
                f"{person.summary()} · last seen {person.last_seen_location or 'unknown'}",
                data={"summary": person.summary(), "is_minor": person.is_minor,
                      "origin": {"lat": origin[0], "lng": origin[1]},
                      "language": person.spoken_language})

    cands = claude.rerank_candidates(person, matching.rank_candidates(person, k=5))
    top = cands[0] if cands else None
    yield _step(2, "match", f"Scanned every centre — {len(cands)} candidate(s)",
                (f"Top: {top.candidate_summary} · {round(top.final_score * 100)}%"
                 if top else "No match above threshold yet"),
                data={"candidates": [c.model_dump() for c in cands]})

    nearby = _nearby(*origin)
    drift = _predict_zones(person, origin, nearby)
    zones = drift.get("zones", [])
    yield _step(3, "predict", f"Predicted {len(zones)} likely drift zone(s)",
                drift.get("rationale", ""), data={"zones": zones, "origin": {"lat": origin[0], "lng": origin[1]}})

    dispatch = _dispatch(person, zones, cands)
    title = ("Private staff alert (minor)" if dispatch["blocked"]
             else {"reunification_announce": "Dispatched reunification announcement",
                   "staff_bolo": "Dispatched staff BOLO"}.get(dispatch["action"], "Dispatched"))
    yield _step(4, "dispatch", title, dispatch["text"], data=dispatch)

    verdict = _verdict(person, cands)
    yield _step(5, "verdict", verdict["title"], verdict["detail"], data=verdict)
