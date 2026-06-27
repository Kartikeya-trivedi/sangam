"""Officials dashboard data (spec §7, §11). Mounted under /ops in main.py."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from db import faiss_index
from models import ConfirmRequest
from safety import audit, staff_alerts

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
    """GeoJSON of cases clustered by centre/ghat for MapLibre (§11 live map)."""
    features = []
    for p in faiss_index.all_persons():
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": _centre_coord(p.centre_id)},
                "properties": {
                    "id": p.id,
                    "role": p.role,
                    "is_minor": p.is_minor,
                    "centre_id": p.centre_id,
                    "summary": p.native_summary,
                },
            }
        )
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


# Demo centre coordinates around the Sangam, Prayagraj (lng, lat). TODO: real per-centre geo.
_CENTRES: dict[Optional[str], list[float]] = {
    "centre-1": [81.8807, 25.4358],
    "centre-7": [81.8850, 25.4290],
    None: [81.8830, 25.4320],
}


def _centre_coord(centre_id: Optional[str]) -> list[float]:
    return _CENTRES.get(centre_id, _CENTRES[None])
