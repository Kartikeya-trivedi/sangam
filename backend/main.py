"""SETU backend — FastAPI app. Run from backend/:  uv/uvicorn main:app --reload --port 8000

SQLite-backed. Boots and serves with zero API keys (Claude/Sarvam/InsightFace degrade).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import safety
from config import settings
from constants import CENTRES
from db import init_db
from routers import announce, dispatcher, intake, match, ops
from services import claude, faces, speech


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    safety.purge_expired()  # housekeeping on boot
    yield


app = FastAPI(title="SETU — Missing-Persons Reunification", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(intake.router)
app.include_router(match.router)
app.include_router(ops.router)
app.include_router(announce.router)
app.include_router(dispatcher.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "db": settings.db_path,
        "offline_mode": settings.offline_mode,
        "capabilities": {
            "claude": claude._get_client() is not None,
            "sarvam_speech": speech.available(),
            "insightface": faces.available(),
        },
    }


@app.get("/api/v1/centres")
def centres():
    """The 10 reporting centres (name + slug + coords) — for intake dropdowns and nearby lookup."""
    from services.geo import CENTRE_COORDS

    out = []
    for name, slug in CENTRES.items():
        coord = CENTRE_COORDS.get(slug)
        out.append({"name": name, "slug": slug,
                    "lat": coord[0] if coord else None, "lng": coord[1] if coord else None})
    return {"centres": out}
