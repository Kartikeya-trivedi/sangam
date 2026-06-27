"""Cross-center duplicate detection (entity resolution) for missing-person records.

This is the dataset's hero problem (see DATA.md): the SAME person reported at multiple centers.
Works on the native dataset schema (name, demographics, language, location, time) with NO photos
and NO external API calls — pure stdlib, fast, fully offline. It lives ALONGSIDE the live
face/attribute matcher in matching.py ("dataset on top, not instead of"): use matching.py for
voice/photo intake, and this module for record-vs-record identity resolution + the dedup eval
(scripts/eval_dedup.py), which scores it against the is_duplicate_report ground truth.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional


@dataclass
class Record:
    case_id: str
    name: str
    gender: str
    age_band: str            # raw dataset band, e.g. "61-70"
    state: str
    district: str
    language: str
    last_seen_location: str
    centre_id: str           # reporting_center
    reported_at: Optional[datetime]
    is_duplicate: bool       # ground truth (is_duplicate_report)


def _dt(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def load_records(path: str) -> list[Record]:
    """Read the synthetic missing-person CSV into Records."""
    out: list[Record] = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(
                Record(
                    case_id=(r.get("case_id") or "").strip(),
                    name=(r.get("missing_person_name") or "").strip(),
                    gender=(r.get("gender") or "").strip().lower(),
                    age_band=(r.get("age_band") or "").strip(),
                    state=(r.get("state") or "").strip().lower(),
                    district=(r.get("district") or "").strip().lower(),
                    language=(r.get("language") or "").strip().lower(),
                    last_seen_location=(r.get("last_seen_location") or "").strip().lower(),
                    centre_id=(r.get("reporting_center") or "").strip(),
                    reported_at=_dt(r.get("reported_at", "")),
                    is_duplicate=(r.get("is_duplicate_report", "").strip().lower() == "true"),
                )
            )
    return out


def _name_sim(a: str, b: str) -> Optional[float]:
    if not a or not b:
        return None  # missing on one side -> don't score name, don't penalize
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# Weights for fields present on BOTH records; renormalized over whatever is available.
_W = {
    "name": 0.40,
    "district": 0.18,
    "language": 0.15,
    "last_seen_location": 0.12,
    "age_band": 0.08,
    "state": 0.07,
}


def dedup_score(a: Record, b: Record) -> float:
    """0..1 likelihood the two records are the SAME person. Symmetric."""
    num = den = 0.0

    ns = _name_sim(a.name, b.name)
    if ns is not None:
        num += _W["name"] * ns
        den += _W["name"]

    for field in ("district", "language", "last_seen_location", "age_band", "state"):
        av, bv = getattr(a, field), getattr(b, field)
        if av and bv:
            num += _W[field] * (1.0 if av == bv else 0.0)
            den += _W[field]

    base = num / den if den else 0.0

    # Small temporal bonus: the same person reported at two centers tends to be close in time.
    if a.reported_at and b.reported_at:
        hours = abs((a.reported_at - b.reported_at).total_seconds()) / 3600.0
        if hours <= 48:
            base = min(1.0, base + 0.08 * (1 - hours / 48))
    return base


def _block_key(r: Record) -> tuple:
    # Blocking: a real duplicate shares gender + age band. Cuts ~2500^2 to a few hundred k.
    return (r.gender, r.age_band)


def best_cross_center(rec: Record, pool: list[Record]) -> tuple[Optional[Record], float]:
    """Best-scoring DIFFERENT-center match for rec (a duplicate is the same person elsewhere)."""
    best, best_s = None, 0.0
    for c in pool:
        if c.case_id == rec.case_id or c.centre_id == rec.centre_id:
            continue
        s = dedup_score(rec, c)
        if s > best_s:
            best, best_s = c, s
    return best, best_s


def best_scores(records: list[Record]) -> list[tuple[Record, Optional[Record], float]]:
    """For every record, its best cross-center candidate + score (with blocking)."""
    buckets: dict[tuple, list[Record]] = {}
    for r in records:
        buckets.setdefault(_block_key(r), []).append(r)
    return [(r, *best_cross_center(r, buckets[_block_key(r)])) for r in records]
