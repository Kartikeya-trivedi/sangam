"""Combined scoring engine (spec §9): face + attribute + geo -> ranked MatchResults.

Never a hard binary match — always top-K with a confidence score, because real intake
data is messy. Claude then re-ranks the top ~10 and writes the human explanation
(services/claude.py: rerank_candidates).

Vector search: central path queries pgvector; offline path queries local FAISS. Same
Person records, two indices. This scaffold ranks against the local store (faiss_index).
"""
from __future__ import annotations

import numpy as np

from db import faiss_index
from models import MatchResult, Person

# Attribute weights (spec §9: age/gender high; clothing/distinguishing medium; height/lang low).
_ATTR_WEIGHTS = {
    "age_band": 3.0,
    "gender": 3.0,
    "clothing": 2.0,
    "distinguishing": 2.0,
    "height_band": 1.0,
    "languages_spoken": 1.0,
}


def cosine(a, b) -> float:
    va, vb = np.asarray(a, "float32"), np.asarray(b, "float32")
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    return 0.0 if na == 0 or nb == 0 else float(np.dot(va, vb) / (na * nb))


def _set_overlap(a: list[str], b: list[str]) -> float:
    sa, sb = {x.lower() for x in a}, {x.lower() for x in b}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def weighted_attribute_overlap(q: Person, c: Person) -> float:
    """0..1 weighted overlap over structured fields, only counting fields both sides have."""
    total = got = 0.0
    for field, w in _ATTR_WEIGHTS.items():
        qv, cv = getattr(q, field), getattr(c, field)
        if isinstance(qv, list):
            if qv and cv:
                total += w
                got += w * _set_overlap(qv, cv)
        else:
            if qv not in (None, "unknown") and cv not in (None, "unknown"):
                total += w
                got += w * (1.0 if qv == cv else 0.0)
    return got / total if total else 0.0


def geo_proximity(q: Person, c: Person) -> float:
    """0..1 from last_seen_location/centre. Same=1.0, token-overlap=0.6, unknown=neutral 0.5."""
    ql = (q.last_seen_location or "").strip().lower()
    cl = (c.last_seen_location or "").strip().lower()
    if not ql or not cl:
        return 0.5  # neutral when unknown
    if ql == cl:
        return 1.0
    return 0.6 if set(ql.split()) & set(cl.split()) else 0.2


def score(query: Person, cand: Person) -> MatchResult:
    both_faces = bool(query.face_embedding) and bool(cand.face_embedding)
    face = cosine(query.face_embedding, cand.face_embedding) if both_faces else None
    attr = weighted_attribute_overlap(query, cand)
    geo = geo_proximity(query, cand)

    # If face available, it dominates; else lean on attributes (spec §9).
    if face is not None:
        final = 0.6 * face + 0.3 * attr + 0.1 * geo
    else:
        final = 0.7 * attr + 0.3 * geo

    return MatchResult(
        person_id=cand.id,
        score=round(final, 4),
        face_score=round(face, 4) if face is not None else None,
        attr_score=round(attr, 4),
        geo_score=round(geo, 4),
        is_minor=cand.is_minor,
        centre_id=cand.centre_id,
        native_summary=cand.native_summary,
        photo_ref=cand.photo_ref,
        explanation="",  # filled by Claude re-rank
    )


def rank_candidates(query: Person, k: int = 10) -> list[MatchResult]:
    """Score the query against the opposite-role records in the local store; return top-K."""
    opposite = "found" if query.role == "lost" else "lost"
    results = [score(query, c) for c in faiss_index.all_persons(role=opposite)]
    results.sort(key=lambda m: m.score, reverse=True)
    return results[:k]
