"""Match refresh (spec §7): GET /match/{report_id} — re-run / refresh ranking."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from db import faiss_index
from services import claude, matching

router = APIRouter()


@router.get("/match/{report_id}")
def get_match(report_id: str):
    person = faiss_index.get_person(report_id)
    if person is None:
        raise HTTPException(status_code=404, detail="report_not_found")
    candidates = matching.rank_candidates(person, k=10)
    candidates = claude.rerank_candidates(person, candidates)
    return {"candidates": candidates}
