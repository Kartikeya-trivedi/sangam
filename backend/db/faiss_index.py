"""Local offline store + vector index (spec §13 edge mode).

Scaffold implementation: an in-memory Person store with brute-force cosine search
(numpy). Swap the search for `faiss.IndexFlatIP` over L2-normalized vectors when you
wire the real index — the public API here stays identical. Also holds the sync queue
of records created offline, to be pushed to Supabase when connectivity returns.

This store is what makes the "pull the network cable" demo (§13 mic-drop) work: all
intake, face matching, and attribute matching run here with no internet.
"""
from __future__ import annotations

import numpy as np

from models import Person

# In-memory store: id -> Person
_persons: dict[str, Person] = {}
# Records created while offline, awaiting push to the central store.
_sync_queue: list[str] = []


def add_person(person: Person, queue_for_sync: bool = True) -> None:
    _persons[person.id] = person
    if queue_for_sync:
        _sync_queue.append(person.id)


def get_person(person_id: str) -> Person | None:
    return _persons.get(person_id)


def all_persons(role: str | None = None) -> list[Person]:
    return [p for p in _persons.values() if role is None or p.role == role]


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype="float32"), np.asarray(b, dtype="float32")
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def search_by_embedding(embedding: list[float], k: int = 10, role: str = "found") -> list[tuple[Person, float]]:
    """Return up to k (Person, face_score) candidates of the given role, best first."""
    scored = [
        (p, _cosine(embedding, p.face_embedding))
        for p in _persons.values()
        if p.role == role and p.face_embedding
    ]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:k]


def pending_sync() -> list[str]:
    return list(_sync_queue)


def clear_sync_queue() -> None:
    _sync_queue.clear()
