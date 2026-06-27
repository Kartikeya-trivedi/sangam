"""Central store: Supabase Postgres + pgvector (spec §6, §9 central path).

Thin wrapper around the supabase client. When credentials are absent or the app is in
offline mode, every call no-ops / returns empty so the local FAISS path (faiss_index.py)
transparently takes over — callers never branch on connectivity.

TODO (Phase 1): implement the real inserts/queries against the `persons` table.
"""
from __future__ import annotations

from typing import Any, Optional

from config import settings
from models import MatchResult, Person

try:
    from supabase import Client, create_client  # type: ignore
except Exception:  # library optional at scaffold time
    create_client = None
    Client = Any  # type: ignore

_client: Optional["Client"] = None


def get_client():
    """Lazily create the Supabase client, or None if unconfigured/offline."""
    global _client
    if not settings.has_supabase or create_client is None:
        return None
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def insert_person(person: Person, centre_id: str | None = None) -> None:
    """Persist a Person row (profile jsonb + face_embedding vector)."""
    client = get_client()
    if client is None:
        return
    # TODO: map Person -> persons row and insert; store embedding in the vector column.
    #   client.table("persons").insert({
    #       "id": person.id, "role": person.role, "profile": person.model_dump(mode="json"),
    #       "face_embedding": person.face_embedding, "is_minor": person.is_minor,
    #       "centre_id": centre_id, "ttl_expires_at": person.ttl_expires_at, ...
    #   }).execute()
    return


def search_by_embedding(embedding: list[float], k: int = 10, role: str = "found") -> list[MatchResult]:
    """Cosine search over pgvector (`<=>`). Returns candidates (face_score populated)."""
    client = get_client()
    if client is None:
        return []
    # TODO: call an RPC / SQL doing `order by face_embedding <=> $1 limit k` filtered by role.
    return []


def fetch_open_persons(role: str = "found") -> list[Person]:
    """Pull open records for attribute-only matching / reverse matching."""
    client = get_client()
    if client is None:
        return []
    # TODO: select * from persons where status='open' and role=$1
    return []
