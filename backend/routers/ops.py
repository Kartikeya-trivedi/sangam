"""Officials dashboard data (spec §7, §11). Mounted under /ops in main.py."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from db import faiss_index
from models import ConfirmRequest
from safety import audit, is_minor, staff_alerts
from services import geo

router = APIRouter()


@router.get("/cases")
def cases(status: Optional[str] = None, centre_id: Optional[str] = None):
    """All open/matched/reunited cases, filterable by centre (§11 case queue)."""
    rows = []
    for p in faiss_index.all_persons():
        if centre_id and p.centre_id != centre_id:
            continue
        if status and p.status != status:
            continue
        rows.append(
            {
                "id": p.id,
                "role": p.role,
                "status": p.status,
                "is_minor": p.is_minor,
                "centre_id": p.centre_id,
                "native_summary": p.native_summary,
                "age_band": p.age_band,
                "gender": p.gender,
                "clothing": p.clothing,
            }
        )
    return {"cases": rows, "staff_alerts": staff_alerts()}


@router.get("/map")
def case_map():
    """Privacy-aware GeoJSON for the live map (§11, §12).

    Lost reports pin where the person was last seen; found reports pin the centre that holds
    them ("in our care"). Minors are redacted to a generic label; no phone/PII is ever returned.
    """
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": _resolve_coord(p)},
            "properties": _safe_props(p),
        }
        for p in faiss_index.all_persons()
    ]
    return {"type": "FeatureCollection", "features": features}


@router.post("/confirm")
def confirm(req: ConfirmRequest):
    """Staff confirm a match -> status=reunited + audit (§7, §11, §12.6)."""
    lost = faiss_index.get_person(req.report_id)
    found = faiss_index.get_person(req.matched_person_id)
    for p in (lost, found):
        if p is not None:
            p.status = "reunited"
    # TODO: persist status to the central store as well.
    audit(req.actor, "confirm_match", req.report_id, matched=req.matched_person_id)
    return {"status": "reunited", "report_id": req.report_id, "matched_person_id": req.matched_person_id}


# --- Geo resolution for the map (Nashik–Trimbakeshwar; coordinates are lng, lat) ---
_NASHIK = [73.7898, 19.9975]

# A few reporting centres map to known landmarks; the rest fall back to the Nashik centroid.
_CENTRE_KEYWORD = {
    "Adgaon Kho-Ya-Paya": "adgaon",
    "Rajur Bahula Center": "rajur bahula",
    "Panchavati Center": "panchavati",
    "Ramkund Kho-Ya-Paya Kendra": "ramkund",
    "Trimbakeshwar Kho-Ya-Paya Kendra": "trimbak",
    "Nashik Road Center": "nashik road",
}
_CENTRE_COORDS: dict[str, list[float]] = {}


def _centre_coord(centre_id: Optional[str]) -> list[float]:
    if not centre_id:
        return _NASHIK
    if centre_id not in _CENTRE_COORDS:
        kw = _CENTRE_KEYWORD.get(centre_id)
        hit = geo.geocode_location(kw) if kw else None
        _CENTRE_COORDS[centre_id] = [hit["lng"], hit["lat"]] if hit else _NASHIK
    return _CENTRE_COORDS[centre_id]


def _jitter(coord: list[float], seed: str) -> list[float]:
    # Deterministic ~tens-of-metres spread so multiple pins at one place don't stack.
    h = abs(hash(seed))
    return [coord[0] + ((h % 100) - 50) / 8000.0, coord[1] + ((h // 100 % 100) - 50) / 8000.0]


def _resolve_coord(p) -> list[float]:
    if p.role == "found":
        base = _centre_coord(p.centre_id)  # held "in our care" at the centre
    else:
        hit = geo.geocode_location(p.last_seen_location or "")
        base = [hit["lng"], hit["lat"]] if hit else _centre_coord(p.centre_id)
    return _jitter(base, p.id)


def _safe_props(p) -> dict:
    """Privacy-safe map properties (§12): minors redacted, no phone/PII ever returned."""
    minor = is_minor(p)
    kind = "reunited" if p.status == "reunited" else ("in_care" if p.role == "found" else "last_seen")
    label = "Protected case (minor) — staff only" if minor else (p.native_summary or f"{p.role} case")
    return {
        "id": p.id,
        "kind": kind,
        "role": p.role,
        "status": p.status,
        "is_minor": minor,
        "centre_id": p.centre_id or "",
        "label": label,
    }


@router.get("/geo")
def geo_layers():
    """Context layers for the map: very-high-risk hotspots + police stations (§13, DATA.md)."""

    def fc(items, props):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [it["lng"], it["lat"]]},
                    "properties": props(it),
                }
                for it in items
            ],
        }

    return {
        "hotspots": fc(geo.list_hotspots(), lambda it: {"name": it["name"], "risk": it["risk"]}),
        "police": fc(geo.police_stations(), lambda it: {"name": it["name"]}),
    }
