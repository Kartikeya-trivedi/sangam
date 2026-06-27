"""Seed the SETU SQLite registry from Synthetic_Missing_Persons_2500.csv.

Maps the dataset into the canonical Person schema and splits it into a cross-center registry of
"lost" (families searching) and "found" (logged at a camp) records, so the matcher and ops
dashboard have a realistic 2,500-record surface.

Grounded in the data analysis:
  - physical_description is IGNORED (it's noise — 24 templates describing random people).
    Seeded records carry no clothing/features; matching leans on age+gender+name+language+geo.
  - reporting_center -> centre_id slug; the original case_id is reused as the record id.
  - reported_at -> created_at + last_seen_time; TTL = created_at + TTL_DAYS.

Run from backend/:  ./.venv/bin/python ../scripts/seed_dataset.py
No Claude/Sarvam calls — pure field mapping, fast.
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from config import settings  # noqa: E402
from constants import is_minor_band, slugify_centre  # noqa: E402
from db import init_db, repo, reset_db  # noqa: E402
from models import Person  # noqa: E402

_CSV = Path(__file__).resolve().parents[1] / "data" / "Synthetic_Missing_Persons_2500.csv"
_FOUND_TARGET = 300  # PRD §6.1: take 300 logged-at-camp "found" records
_STATUS_MAP = {"Reunited": "reunited", "Pending": "open",
               "Transferred to hospital": "open", "Unresolved": "open"}


def _blank(v: str | None) -> str | None:
    v = (v or "").strip()
    return v or None


def _parse_dt(s: str | None) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _row_to_person(row: dict, role: str) -> Person:
    name = _blank(row.get("missing_person_name"))
    gender = (row.get("gender") or "unknown").strip().lower()
    gender = gender if gender in ("male", "female") else "unknown"
    age_band = (row.get("age_band") or "unknown").strip()
    language = _blank(row.get("language"))
    location = _blank(row.get("last_seen_location"))
    created = _parse_dt(row.get("reported_at")) or datetime.now(timezone.utc)
    summary = (f"{name or 'A person'}, {age_band} {gender}"
               + (f", speaks {language.lower()}" if language else "")
               + (f", last seen at {location}" if location else "") + ".")
    status = "open" if role == "found" else _STATUS_MAP.get((row.get("status") or "").strip(), "open")
    return Person(
        id=row["case_id"],  # reuse the dataset id for traceability
        role=role,  # type: ignore[arg-type]
        age_band=age_band,  # type: ignore[arg-type]
        gender=gender,  # type: ignore[arg-type]
        name=name,
        languages_spoken=[language.lower()] if language else [],
        last_seen_location=location,
        last_seen_time=created,
        reporter_mobile=_blank(row.get("reporter_mobile")),
        spoken_language=(language or "unknown").lower(),
        raw_transcript=summary,
        native_summary=summary,
        is_minor=is_minor_band(age_band),
        consent_given=True,
        centre_id=slugify_centre(row.get("reporting_center") or ""),
        status=status,  # type: ignore[arg-type]
        created_at=created,
        ttl_expires_at=created + timedelta(days=settings.ttl_days),
    )


def main() -> None:
    if not _CSV.exists():
        raise SystemExit(f"dataset not found: {_CSV}")
    init_db()
    reset_db()
    rows = list(csv.DictReader(_CSV.open(newline="", encoding="utf-8")))

    # PRD §6.1: first 300 Reunited/Pending rows become "found"; the rest stay "lost".
    found_ids, count = set(), 0
    for r in rows:
        if count >= _FOUND_TARGET:
            break
        if (r.get("status") or "").strip() in ("Reunited", "Pending"):
            found_ids.add(r["case_id"])
            count += 1

    persons = [_row_to_person(r, "found" if r["case_id"] in found_ids else "lost") for r in rows]
    repo.insert_many(persons)

    # summary
    by_role = {"lost": 0, "found": 0}
    by_status: dict[str, int] = {}
    minors = 0
    for p in persons:
        by_role[p.role] += 1
        by_status[p.status] = by_status.get(p.status, 0) + 1
        minors += p.is_minor
    print(f"Seeded {len(persons)} records into {settings.db_path}")
    print(f"  by role:   {by_role}")
    print(f"  by status: {by_status}")
    print(f"  minors:    {minors}")
    print(f"  open lost / open found (matchable surface): "
          f"{repo.list_persons(role='lost', status='open', per_page=1)[1]} / "
          f"{repo.list_persons(role='found', status='open', per_page=1)[1]}")


if __name__ == "__main__":
    main()
