"""Seed demo 'found' person records so the demo has something to match against (spec §15).

Run after the backend is up:
    python scripts/seed_found_persons.py

Posts a few found-person reports (text intake) to the running API. Includes a minor case
to demo the child-safety branch (§12) and a Tamil/Marathi pair to demo cross-language (§8).
"""
from __future__ import annotations

import os

import requests

API = os.environ.get("SETU_API", "http://localhost:8000")

FOUND = [
    {
        "text": "Elderly man, blue kurta, speaks Tamil, found near Sangam ghat",
        "centre_id": "centre-7",
        "language_hint": "en-IN",
    },
    {
        "text": "Buzurg aadmi, white dhoti, speaks Marathi, near Centre 1",
        "centre_id": "centre-1",
        "language_hint": "en-IN",
    },
    {
        "text": "Young woman, green saree, speaks Telugu, near the bathing area",
        "centre_id": "centre-7",
        "language_hint": "en-IN",
    },
    {
        "text": "Child, red shirt, crying, brought to lost-and-found",
        "centre_id": "centre-1",
        "language_hint": "en-IN",
    },
]


def main() -> None:
    for f in FOUND:
        r = requests.post(f"{API}/report/found", data=f, timeout=30)
        r.raise_for_status()
        out = r.json()
        print(f"seeded {out['report_id']}  minor={out['structured']['is_minor']}  {f['text'][:42]}")
    print(f"\nDone. {len(FOUND)} found-persons loaded at {API}.")


if __name__ == "__main__":
    main()
