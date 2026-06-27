"""Seed a small, map-friendly demo into a running backend (spec §11, §12).

    uv run python scripts/seed_map_demo.py

Posts lost reports at known landmarks (pin "last seen here") and found reports held at centres
(pin "in our care"), including a MINOR case to show the privacy redaction on the map. Then open
the Ops dashboard → Map. Pairs with docs/MAP.md.
"""
from __future__ import annotations

import os

import requests

API = os.environ.get("SETU_API", "http://localhost:8000")

LOST = [
    {"text": "Elderly man, blue kurta, Tamil speaker, last seen near Ramkund", "language_hint": "en-IN"},
    {"text": "Old woman, green saree, last seen at Panchavati", "language_hint": "en-IN"},
    {"text": "Man with walking stick, last seen near Trimbakeshwar", "language_hint": "en-IN"},
]

FOUND = [
    {"text": "Elderly man, blue kurta, speaks Tamil, in our care", "centre_id": "Trimbakeshwar Kho-Ya-Paya Kendra", "language_hint": "en-IN"},
    {"text": "Child, red shirt, crying, brought to centre near Nashik Road", "centre_id": "Nashik Road Center", "language_hint": "en-IN"},
    {"text": "Woman, green saree, with us at the centre", "centre_id": "Panchavati Center", "language_hint": "en-IN"},
]


def post(role: str, payload: dict) -> None:
    r = requests.post(f"{API}/report/{role}", data=payload, timeout=30)
    r.raise_for_status()
    out = r.json()
    print(f"{role:5} {out['report_id'][:8]}  minor={out['structured']['is_minor']}  {payload['text'][:46]}")


def main() -> None:
    for p in LOST:
        post("lost", p)
    for p in FOUND:
        post("found", p)
    print(f"\nSeeded {len(LOST)} lost + {len(FOUND)} found at {API}. Open Ops dashboard → Map.")


if __name__ == "__main__":
    main()
