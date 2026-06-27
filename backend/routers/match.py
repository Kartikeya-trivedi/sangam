"""Re-run matching for an existing report (dashboard refresh / new records arrived)."""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from db import repo
from services import intake

router = APIRouter(prefix="/api/v1/match", tags=["match"])


@router.get("/{report_id}")
def get_matches(report_id: str, top_k: int = Query(5, ge=1, le=20),
                min_score: float = Query(0.3, ge=0.0, le=1.0)):
    if repo.get_person(report_id) is None:
        return JSONResponse(status_code=404, content={"error": "report_not_found"})
    candidates = intake.rematch(report_id, top_k=top_k, min_score=min_score)
    return {"report_id": report_id, "candidates": [c.model_dump(mode="json") for c in candidates]}
