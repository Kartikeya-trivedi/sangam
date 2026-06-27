"""Deterministic seed for the demo + Playwright E2E.

Inserts a small, fixed set of people — named FOUND persons (incl. one minor, whose name the
ops dashboard redacts) and matching named LOST persons, so cases show real names and Sahayak
has strong named matches to work. Pure DB writes: no API keys, no running server, no network.

Idempotent: re-running only replaces the `e2e-*` rows, leaving any other data untouched.

Run from backend/:  uv run python ../scripts/seed_e2e.py
"""
from __future__ import annotations

import pathlib
import sys

_BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from db import init_db, repo  # noqa: E402
from db.connection import get_conn  # noqa: E402
from models import Person  # noqa: E402

# Named FOUND persons currently in our care at help desks.
FOUND: list[Person] = [
    Person(
        id="e2e-found-001", role="found", name="Ramesh Kumar", age_band="71-80", gender="male",
        languages_spoken=["tamil"], clothing=["blue kurta"], last_seen_location="Ramkund Ghat",
        centre_id="ramkund_kho_ya_paya_kendra", status="open", consent_given=True,
        native_summary="Elderly man, blue kurta, speaks Tamil — safe at Ramkund help desk.",
    ),
    Person(
        id="e2e-found-002", role="found", name="Lakshmi Devi", age_band="18-40", gender="female",
        languages_spoken=["hindi"], clothing=["green saree"], last_seen_location="Panchavati Circle",
        centre_id="panchavati_center", status="open", consent_given=True,
        native_summary="Young woman, green saree — safe at Panchavati centre.",
    ),
    Person(
        id="e2e-found-003", role="found", name="Arjun", age_band="0-12", gender="male",
        languages_spoken=["marathi"], clothing=["red shirt"], last_seen_location="Trimbak Road",
        centre_id="trimbakeshwar_kho_ya_paya_kendra", status="open", consent_given=True,
        is_minor=True,  # name is redacted on the dashboard (child-safety §12)
        native_summary="Small boy, red shirt — in protective care; guardian verification required.",
    ),
]

# Matching named LOST reports filed by families — strong named matches for Sahayak to work.
LOST: list[Person] = [
    Person(
        id="e2e-lost-001", role="lost", name="Ramesh Kumar", age_band="71-80", gender="male",
        languages_spoken=["tamil"], clothing=["blue kurta"], last_seen_location="Ramkund Ghat",
        centre_id="central_control_room", status="open", consent_given=True,
        reporter_name="Suresh Kumar", reporter_mobile="9876543210",
        native_summary="My father Ramesh, elderly, blue kurta, Tamil — lost near Ramkund.",
    ),
    Person(
        id="e2e-lost-002", role="lost", name="Lakshmi Devi", age_band="18-40", gender="female",
        languages_spoken=["hindi"], clothing=["green saree"], last_seen_location="Panchavati Circle",
        centre_id="central_control_room", status="open", consent_given=True,
        reporter_name="Anita Devi", reporter_mobile="9812345678",
        native_summary="My sister Lakshmi, green saree — lost near Panchavati.",
    ),
]


def main() -> None:
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM persons WHERE id LIKE 'e2e-%'")
    try:
        conn.execute("DELETE FROM persons_fts WHERE person_id LIKE 'e2e-%'")
    except Exception:
        pass
    conn.commit()
    n = repo.insert_many(FOUND + LOST)
    print(f"Seeded {len(FOUND)} named FOUND + {len(LOST)} named LOST persons ({n} total).")


if __name__ == "__main__":
    main()
