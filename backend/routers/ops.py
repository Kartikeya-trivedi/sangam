"""Officials dashboard — confirm/reject, case queue, stats, map, notifications, guardian verify."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

import safety
from constants import AGE_BANDS, CENTRE_SLUGS
from db import repo
from models import ConfirmRequest, GuardianVerifyRequest, RejectRequest
from services import geo, matching

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])


def _is_admin(role_header: str | None) -> bool:
    return (role_header or "").lower() == "admin"


def _hours_open(created_at) -> float:
    if not created_at:
        return 0.0
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    return round((datetime.now(timezone.utc) - created_at).total_seconds() / 3600, 1)


# --- match confirmation / rejection -------------------------------------------------------
@router.post("/confirm")
def confirm(req: ConfirmRequest):
    lost = repo.get_person(req.lost_person_id)
    found = repo.get_person(req.found_person_id)
    if not lost or not found:
        return JSONResponse(status_code=404, content={"error": "person_not_found"})
    if {lost.role, found.role} != {"lost", "found"}:
        return JSONResponse(status_code=400, content={"error": "roles_must_be_opposite"})
    if safety.match_requires_guardian(lost, found) and not req.notes.strip():
        return JSONResponse(status_code=400, content={
            "error": "guardian_verification_required",
            "spoken": "बच्चे की सुरक्षा के लिए अभिभावक सत्यापन ज़रूरी है।"})
    for pid in (lost.id, found.id):
        repo.update_status(pid, "reunited")
    repo.write_audit(req.confirmed_by, "match_confirmed", person_id=lost.id,
                     related_person_id=found.id, meta={"notes_present": bool(req.notes)})
    return {"lost_person_id": lost.id, "found_person_id": found.id, "status": "reunited",
            "confirmed_by": req.confirmed_by, "confirmed_at": datetime.now(timezone.utc).isoformat()}


@router.post("/reject")
def reject(req: RejectRequest):
    repo.write_audit(req.rejected_by, "match_rejected", person_id=req.lost_person_id,
                     related_person_id=req.found_person_id, meta={"reason": req.reason})
    return {"status": "rejected", "lost_person_id": req.lost_person_id,
            "found_person_id": req.found_person_id}


# --- case queue ---------------------------------------------------------------------------
@router.get("/cases")
def cases(status: str | None = None, role: str | None = None, centre_id: str | None = None,
          is_minor: bool | None = None, page: int = Query(1, ge=1),
          per_page: int = Query(50, ge=1, le=200), sort_by: str = "created_at",
          sort_order: str = "desc", x_role: str | None = Header(None)):
    admin = _is_admin(x_role)
    persons, total = repo.list_persons(status=status, role=role, centre_id=centre_id,
                                       is_minor=is_minor, page=page, per_page=per_page,
                                       sort_by=sort_by, sort_order=sort_order)
    out = []
    for p in persons:
        top = matching.rank_candidates(p, k=1)
        case = {
            "id": p.id, "role": p.role, "status": p.status, "age_band": p.age_band,
            "gender": p.gender, "name": p.name, "clothing": p.clothing,
            "languages_spoken": p.languages_spoken, "last_seen_location": p.last_seen_location,
            "centre_id": p.centre_id, "created_at": p.created_at.isoformat() if p.created_at else None,
            "is_minor": p.is_minor, "match_count": len(matching.rank_candidates(p, k=5)),
            "best_match_score": top[0].final_score if top else None,
            "hours_open": _hours_open(p.created_at),
        }
        # Minor PII is admin-only.
        if p.is_minor and not admin:
            case["name"] = None
        out.append(case)
    by_status = repo.count_by("status")
    summary = {
        "total_open": by_status.get("open", 0),
        "total_matched": by_status.get("matched", 0),
        "total_reunited": by_status.get("reunited", 0),
        "total_minor_open": repo.list_persons(status="open", is_minor=True, per_page=1)[1],
    }
    return {"cases": out, "total": total, "page": page, "per_page": per_page, "summary": summary}


# --- map ----------------------------------------------------------------------------------
_CHOKE_RISK = {"No-vehicle pressure zone": "very-high", "Traffic choke point": "high",
               "Transfer node": "high"}


@router.get("/map")
def map_data():
    features = []
    # case clusters per centre
    for slug in CENTRE_SLUGS:
        coord = geo.CENTRE_COORDS.get(slug)
        if not coord:
            continue
        open_lost = repo.list_persons(role="lost", status="open", centre_id=slug, per_page=1)[1]
        open_found = repo.list_persons(role="found", status="open", centre_id=slug, per_page=1)[1]
        features.append({"type": "Feature",
                         "geometry": {"type": "Point", "coordinates": [coord[1], coord[0]]},
                         "properties": {"feature_type": "case_cluster", "centre_id": slug,
                                        "open_lost": open_lost, "open_found": open_found}})
    for c in geo.chokepoints():
        features.append({"type": "Feature",
                         "geometry": {"type": "Point", "coordinates": [c["lng"], c["lat"]]},
                         "properties": {"feature_type": "chokepoint", "category": c["category"],
                                        "location_name": c["location_name"],
                                        "risk_level": _CHOKE_RISK.get(c["category"], "medium")}})
    for s in geo.police_stations():
        features.append({"type": "Feature",
                         "geometry": {"type": "Point", "coordinates": [s["lng"], s["lat"]]},
                         "properties": {"feature_type": "police_station",
                                        "station_name": s["station_name"]}})
    for z in geo.zones():
        features.append({"type": "Feature",
                         "geometry": {"type": "Point", "coordinates": [z["lng"], z["lat"]]},
                         "properties": {"feature_type": "zone", "zone_name": z["zone_name"],
                                        "boundary_points": z["boundary_points"]}})
    return {"type": "FeatureCollection", "features": features}


# --- stats --------------------------------------------------------------------------------
@router.get("/stats")
def stats():
    by_status = repo.count_by("status")
    by_age = repo.count_by("age_band")
    total = sum(by_status.values())
    by_centre = []
    for slug in sorted(CENTRE_SLUGS):
        tot = repo.list_persons(centre_id=slug, per_page=1)[1]
        if tot:
            by_centre.append({"centre_id": slug, "total_cases": tot,
                              "open": repo.list_persons(centre_id=slug, status="open", per_page=1)[1],
                              "reunited": repo.list_persons(centre_id=slug, status="reunited", per_page=1)[1]})
    return {
        "overall": {"total_reports": total, "by_status": by_status,
                    "total_reunited": by_status.get("reunited", 0),
                    "total_open": by_status.get("open", 0)},
        "by_centre": by_centre,
        "by_age_band": [{"age_band": b, "total": by_age.get(b, 0),
                         "pct_of_total": round(100 * by_age.get(b, 0) / total, 1) if total else 0}
                        for b in AGE_BANDS],
        "notifications": len(repo.list_notifications(status="new")),
    }


@router.get("/notifications")
def notifications(status: str | None = "new"):
    return {"notifications": repo.list_notifications(status=status)}


# --- guardian verification (minor safety) -------------------------------------------------
@router.post("/guardian-verify")
def guardian_verify(req: GuardianVerifyRequest):
    minor = repo.get_person(req.minor_person_id)
    if not minor:
        return JSONResponse(status_code=404, content={"error": "person_not_found"})
    if not minor.is_minor:
        return JSONResponse(status_code=400, content={"error": "not_a_minor"})
    action = "guardian_verification_completed" if req.approved else "guardian_verification_failed"
    repo.write_audit(req.verifier_name, action, person_id=minor.id,
                     related_person_id=req.claimant_person_id,
                     meta={"method": req.verification_method, "approved": req.approved})
    if req.approved:
        for pid in (req.minor_person_id, req.claimant_person_id):
            repo.update_status(pid, "reunited")
        repo.write_audit(req.verifier_name, "match_confirmed", person_id=minor.id,
                         related_person_id=req.claimant_person_id, meta={"guardian_verified": True})
        return {"status": "reunited", "guardian_verified": True}
    return {"status": "police_escalation", "guardian_verified": False}
