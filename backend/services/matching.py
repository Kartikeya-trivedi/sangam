"""The matching engine — face + attribute + geo -> ranked, explained candidates.

Design is grounded in the data analysis: physical descriptions are noise, names are often
absent, state/language are random. So the engine leans on the *reliable* signals (age, gender,
name-when-present, geo) and treats weak signals weakly. It is never a hard binary — always a
ranked top-K with a transparent per-signal breakdown a volunteer can sanity-check.

Two hard rules:
  1. Gender mismatch (both known, different) => final_score = 0. The one veto.
  2. A signal that doesn't apply (e.g. no name on either side) is dropped and its weight is
     redistributed across the applicable signals — missing data must not silently penalise.

Staged retrieval (rank_candidates): SQL pre-filter (repo.candidates_for) -> Python scoring ->
sort. Claude re-rank of the top ~10 happens one layer up (routers/services.claude).
"""
from __future__ import annotations

import numpy as np

from config import settings
from constants import age_band_distance
from models import MatchResult, Person, ScoreBreakdown
from services import geo
from services.names import name_similarity

# Nominal signal weights. Face is dominant when present; when a signal is N/A its weight is
# redistributed across the rest (see _combine). These ratios encode the analysis priorities.
_WEIGHTS = {
    "face": 0.40,
    "name": 0.25,
    "age": 0.15,
    "gender": 0.10,
    "language": 0.08,
    "clothing": 0.07,
    "distinguishing": 0.03,
    "location": 0.06,
    "centre": 0.04,
    "time": 0.04,
}


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    va, vb = np.asarray(a, "float32"), np.asarray(b, "float32")
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    return 0.0 if na == 0 or nb == 0 else float(np.dot(va, vb) / (na * nb))


def _set_overlap(a: list[str], b: list[str]) -> float:
    sa = {x.strip().lower() for x in a if x and x.strip()}
    sb = {x.strip().lower() for x in b if x and x.strip()}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _age_score(a: str, b: str) -> float | None:
    d = age_band_distance(a, b)
    if d is None:  # one side unknown -> not applicable
        return None
    return {0: 1.0, 1: 0.6, 2: 0.2}.get(d, 0.0)


def _gender_score(a: str, b: str) -> float:
    if a == "unknown" or b == "unknown":
        return 0.5  # neutral, not a penalty
    return 1.0 if a == b else 0.0  # hard veto handled in compute_match_score


def _language_score(a: list[str], b: list[str]) -> float | None:
    sa = {x.lower() for x in a if x}
    sb = {x.lower() for x in b if x}
    if not sa or not sb:
        return None
    return 1.0 if sa & sb else 0.0


def _time_score(q: Person, c: Person) -> float | None:
    if not q.last_seen_time or not c.last_seen_time:
        return None
    hours = abs((q.last_seen_time - c.last_seen_time).total_seconds()) / 3600.0
    if hours <= 2:
        return 1.0
    if hours <= 6:
        return 0.7
    if hours <= 24:
        return 0.4
    return 0.2


def _confidence(score: float) -> str:
    if score >= settings.high_confidence_threshold:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def compute_match_score(query: Person, candidate: Person) -> MatchResult:
    """Full weighted score between a query and one candidate, with a per-signal breakdown."""
    b = ScoreBreakdown()

    both_faces = bool(query.face_embedding) and bool(candidate.face_embedding)
    if both_faces:
        b.face = round(cosine(query.face_embedding, candidate.face_embedding), 4)

    b.name = name_similarity(query.name, candidate.name)
    b.age = _age_score(query.age_band, candidate.age_band)
    b.gender = _gender_score(query.gender, candidate.gender)
    b.language = _language_score(query.languages_spoken, candidate.languages_spoken)

    clo = _set_overlap(query.clothing, candidate.clothing)
    b.clothing = round(clo, 4) if (query.clothing and candidate.clothing) else None
    dist = _set_overlap(query.distinguishing_features, candidate.distinguishing_features)
    b.distinguishing = round(dist, 4) if (query.distinguishing_features
                                          and candidate.distinguishing_features) else None

    loc_score, loc_ok = geo.geo_proximity(query.last_seen_location, candidate.last_seen_location)
    b.location = round(loc_score, 4) if loc_ok else None
    cen_score, cen_ok = geo.centre_proximity(query.centre_id, candidate.centre_id)
    b.centre = round(cen_score, 4) if cen_ok else None
    b.time = _time_score(query, candidate)

    # Hard veto: definite gender mismatch kills the match.
    gender_veto = (query.gender != "unknown" and candidate.gender != "unknown"
                   and query.gender != candidate.gender)
    final = 0.0 if gender_veto else _combine(b)

    requires_gv = query.is_minor or candidate.is_minor
    return MatchResult(
        candidate_id=candidate.id,
        candidate_role=candidate.role,
        final_score=round(final, 4),
        breakdown=b,
        confidence="low" if gender_veto else _confidence(final),
        is_minor=candidate.is_minor,
        requires_guardian_verification=requires_gv,
        candidate_centre_id=candidate.centre_id,
        candidate_summary=candidate.summary(),
    )


def _combine(b: ScoreBreakdown) -> float:
    """Weighted mean over applicable signals; weights of N/A signals are redistributed."""
    num = den = 0.0
    for signal, w in _WEIGHTS.items():
        v = getattr(b, signal)
        if v is None:
            continue
        num += w * v
        den += w
    return num / den if den else 0.0


def rank_candidates(query: Person, *, candidates: list[Person] | None = None, k: int = 5,
                    min_score: float | None = None) -> list[MatchResult]:
    """Score the query against opposite-role candidates; return top-K above min_score."""
    from db import repo  # local import: matching is import-safe without a live DB

    if candidates is None:
        candidates = repo.candidates_for(query, limit=300)
    floor = settings.review_threshold if min_score is None else min_score
    results = [compute_match_score(query, c) for c in candidates]
    results = [r for r in results if r.final_score >= floor]
    results.sort(key=lambda m: m.final_score, reverse=True)
    return results[:k]
