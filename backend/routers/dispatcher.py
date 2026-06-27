"""Sahayak dispatcher — agentic reunification case-work.

GET /api/v1/ops/dispatch/{report_id}/stream  -> Server-Sent Events, one step at a time (live).
GET /api/v1/ops/dispatch/{report_id}          -> the full step list in one JSON (tests / fallback).
"""
from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services import dispatcher

router = APIRouter(prefix="/api/v1/ops", tags=["dispatch"])


@router.get("/dispatch/{report_id}/stream")
def dispatch_stream(report_id: str, language: str | None = None):
    def gen():
        for step in dispatcher.run(report_id, language):
            yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/dispatch/{report_id}")
def dispatch_json(report_id: str, language: str | None = None):
    return {"report_id": report_id, "steps": list(dispatcher.run(report_id, language))}
