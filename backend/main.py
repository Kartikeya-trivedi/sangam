"""SETU — FastAPI entrypoint.

Run from this directory:  uvicorn main:app --reload --port 8000
Interactive API docs:     http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import announce, intake, match, nav, ops

app = FastAPI(
    title="SETU — Missing-Persons Reunification (Kumbh Mela 2027)",
    version="0.1.0",
    description="Voice-first, cross-language, face + attribute matching across lost-and-found centres.",
)

# Wide-open CORS for the hackathon (pilgrim PWA + ops dashboard on different origins).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake.router, tags=["intake"])
app.include_router(match.router, tags=["match"])
app.include_router(announce.router, tags=["announce"])
app.include_router(nav.router, tags=["nav"])
app.include_router(ops.router, prefix="/ops", tags=["ops"])


@app.get("/health")
def health():
    return {
        "status": "ok",
        "offline_mode": settings.offline_mode,
        "anthropic": settings.has_anthropic,
        "sarvam": settings.has_sarvam,
        "supabase": settings.has_supabase,
    }
