"""Agentic navigation route (spec §11). POST /nav — volunteer asks, Claude routes via geo tools."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services import nav_agent

router = APIRouter()


class NavRequest(BaseModel):
    query: str


@router.post("/nav")
def nav(req: NavRequest):
    return nav_agent.navigate(req.query)
