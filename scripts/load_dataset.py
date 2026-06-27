"""Load the synthetic missing-person dataset into a RUNNING SETU backend (for the demo).

    uv run python scripts/load_dataset.py --limit 300              # seed 300 as 'found'
    uv run python scripts/load_dataset.py --limit 300 --role lost

Posts via the HTTP API so records flow through the normal pipeline (Claude extract -> match).
For the rigorous OFFLINE dedup metric (no server needed) use scripts/eval_dedup.py instead.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from services.dedup import Record, load_records  # noqa: E402

DEFAULT = ROOT / "data" / "Synthetic_Missing_Persons_2500.csv"

# Dataset language name -> Sarvam-style code (best effort; unknown -> hi-IN).
LANG = {
    "hindi": "hi-IN", "marathi": "mr-IN", "tamil": "ta-IN", "telugu": "te-IN",
    "bengali": "bn-IN", "gujarati": "gu-IN", "kannada": "kn-IN", "malayalam": "ml-IN",
    "punjabi": "pa-IN", "bhojpuri": "hi-IN", "maithili": "hi-IN", "awadhi": "hi-IN",
}


def describe(r: Record) -> str:
    bits = [
        r.name or "unknown name",
        r.gender,
        f"age {r.age_band}",
        f"{r.language} speaker",
        f"from {r.district}, {r.state}",
        f"last seen {r.last_seen_location}",
    ]
    return ", ".join(b for b in bits if b and b.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--role", choices=["found", "lost"], default="found")
    ap.add_argument("--csv", default=str(DEFAULT))
    a = ap.parse_args()

    records = load_records(a.csv)[: a.limit]
    endpoint = f"{a.api}/report/{a.role}"
    ok = 0
    for r in records:
        data = {"text": describe(r), "language_hint": LANG.get(r.language, "hi-IN")}
        if a.role == "found":
            data["centre_id"] = r.centre_id
        try:
            resp = requests.post(endpoint, data=data, timeout=30)
            resp.raise_for_status()
            ok += 1
        except Exception as e:
            print(f"  failed {r.case_id}: {e}")
    print(f"Seeded {ok}/{len(records)} records as '{a.role}' into {a.api}")


if __name__ == "__main__":
    main()
