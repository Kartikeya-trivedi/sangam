"""Deterministic seed for the Playwright E2E suite.

Inserts a small, fixed set of FOUND persons (including one minor, for the child-safety path)
straight into the SQLite DB so the ops queue is populated and live-intake reports get a stable
match. No API keys, no running server, no network — pure DB writes.

Idempotent: re-running only replaces the `e2e-*` rows, leaving any other data untouched.

Run from the repo root or anywhere:
    uv run --project backend python scripts/seed_e2e.py
or from backend/:
    uv run python ../scripts/seed_e2e.py
"""
from __future__ import annotations

import pathlib
import sys

# Make the backend package importable regardless of where this is launched from.
_BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from db import init_db, repo  # noqa: E402
from db.connection import get_conn  # noqa: E402
from models import Person  # noqa: E402

# Fixed ids (e2e-*) so re-seeding is idempotent and tests can reference them directly.
FOUND: list[Person] = [
    Person(
        id="e2e-found-001", role="found", age_band="71-80", gender="male",
        languages_spoken=["tamil"], clothing=["blue kurta"], last_seen_location="Ramkund Ghat",
        centre_id="ramkund_kho_ya_paya_kendra", status="open", consent_given=True,
        native_summary="Elderly man, blue kurta, speaks Tamil — safe at Ramkund help desk.",
    ),
    Person(
        id="e2e-found-002", role="found", age_band="18-40", gender="female",
        languages_spoken=["hindi"], clothing=["green saree"], last_seen_location="Panchavati Circle",
        centre_id="panchavati_center", status="open", consent_given=True,
        native_summary="Young woman, green saree — safe at Panchavati centre.",
    ),
    Person(
        id="e2e-found-003", role="found", age_band="0-12", gender="male",
        languages_spoken=["marathi"], clothing=["red shirt"], last_seen_location="Trimbak Road",
        centre_id="trimbakeshwar_kho_ya_paya_kendra", status="open", consent_given=True,
        is_minor=True,  # child-safety path: never publicly announced (§12)
        native_summary="Small boy, red shirt — in protective care; guardian verification required.",
    ),
]


def main() -> None:
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM persons WHERE id LIKE 'e2e-%'")
    try:
        conn.execute("DELETE FROM persons_fts WHERE person_id LIKE 'e2e-%'")
    except Exception:
        pass  # FTS row absent on first run — fine.
    conn.commit()
    n = repo.insert_many(FOUND)
    minors = sum(1 for p in FOUND if p.is_minor)
    print(f"Seeded {n} e2e FOUND persons ({minors} minor) into {conn.execute('PRAGMA database_list').fetchone()[2]}")


if __name__ == "__main__":
    main()
