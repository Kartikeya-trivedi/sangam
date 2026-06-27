"""Generate labelled matching test pairs (the dataset has no true linked duplicates).

For each POSITIVE pair we synthesize the SAME person reported at two different centres, with
realistic perturbation (name variants/dropouts, added clothing, an age estimate that's sometimes
off by one band, a reporting-time lag). For each NEGATIVE pair we synthesize two DIFFERENT people
with confusable demographics (same gender + age band) but different name/language/location.

This gives the matcher a ground-truth set to score against — see eval_matcher.py.

Run from backend/:  ./.venv/bin/python ../scripts/generate_test_pairs.py [n_positive] [n_negative]
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from constants import AGE_BANDS, CENTRE_SLUGS, is_minor_band  # noqa: E402
from db import init_db, repo  # noqa: E402
from models import Person  # noqa: E402
from services import geo  # noqa: E402

RNG = random.Random(20270729)  # deterministic (peak Snan day, for luck)

_FIRST = ["Ramesh", "Lakshmi", "Mohan", "Sita", "Anil", "Geeta", "Vijay", "Radha", "Suresh",
          "Kamla", "Arun", "Meena", "Prakash", "Sunita", "Deepak", "Pushpa", "Rakesh", "Durga"]
_LAST = ["Sharma", "Patil", "Iyer", "Chaudhary", "Reddy", "Dubey", "Singh", "Menon", "Gupta"]
_LANGS = ["hindi", "tamil", "marathi", "telugu", "bengali", "gujarati", "kannada", "bhojpuri"]
_CLOTHES = ["blue kurta", "white dhoti", "red saree", "green saree", "saffron kurta",
            "white shirt", "yellow kurta", "pink frock", "school uniform"]
_FEATURES = ["walking stick", "hearing aid", "spectacles", "limp", "white beard"]
_LOCATIONS = list(geo.LANDMARKS.keys())
_CENTRES = sorted(CENTRE_SLUGS)
_ELDER_BANDS = ["41-60", "61-70", "71-80", "80+"]


def _vowel_swap(name: str) -> str:
    vowels = "aeiou"
    idxs = [i for i, ch in enumerate(name.lower()) if ch in vowels and i > 0]
    if not idxs:
        return name
    i = RNG.choice(idxs)
    repl = RNG.choice([v for v in vowels if v != name[i].lower()])
    return name[:i] + repl + name[i + 1:]


def _perturb_name(name: str) -> str | None:
    r = RNG.random()
    if r < 0.10:
        return None                       # confused elder can't state their name
    if r < 0.30:
        return name                       # exact
    # slight transliteration drift on the given name
    given, *rest = name.split()
    return " ".join([_vowel_swap(given), *rest])


def _adjacent_band(band: str) -> str:
    i = AGE_BANDS.index(band)
    j = min(len(AGE_BANDS) - 1, max(0, i + RNG.choice([-1, 1])))
    return AGE_BANDS[j]


def _person(pid: str, role: str, *, pair_id: str, should_match: int, name, gender, age_band,
            languages, clothing, features, location, centre, created) -> Person:
    return Person(
        id=pid, role=role, age_band=age_band, gender=gender, name=name,
        clothing=clothing, distinguishing_features=features, languages_spoken=languages,
        last_seen_location=location, last_seen_time=created, spoken_language=languages[0] if languages else "unknown",
        raw_transcript=f"{name or 'unknown'} {age_band} {gender} {' '.join(clothing)}",
        native_summary=f"{age_band} {gender}", is_minor=is_minor_band(age_band),
        consent_given=True, centre_id=centre, status="open", created_at=created,
        ttl_expires_at=created + timedelta(days=45),
    )


def _base():
    name = f"{RNG.choice(_FIRST)} {RNG.choice(_LAST)}"
    gender = "female" if name.split()[0] in {"Lakshmi", "Sita", "Geeta", "Radha", "Kamla",
                                             "Meena", "Sunita", "Pushpa", "Durga"} else "male"
    return {
        "name": name, "gender": gender, "age_band": RNG.choice(_ELDER_BANDS),
        "languages": [RNG.choice(_LANGS)], "clothing": RNG.sample(_CLOTHES, 2),
        "features": RNG.sample(_FEATURES, RNG.choice([0, 1])), "location": RNG.choice(_LOCATIONS),
    }


def make_positive(i: int) -> list[Person]:
    b = _base()
    t0 = datetime(2027, 7, 29, RNG.randint(5, 20), RNG.randint(0, 59), tzinfo=timezone.utc)
    centres = RNG.sample(_CENTRES, 2)
    pair = f"pos-{i:03d}"
    lost = _person(f"{pair}-L", "lost", pair_id=pair, should_match=1, name=b["name"],
                   gender=b["gender"], age_band=b["age_band"], languages=b["languages"],
                   clothing=b["clothing"], features=b["features"], location=b["location"],
                   centre=centres[0], created=t0)
    # found = same person, different centre, perturbed
    found_age = b["age_band"] if RNG.random() < 0.9 else _adjacent_band(b["age_band"])
    shared = [b["clothing"][0]] + ([RNG.choice(_CLOTHES)] if RNG.random() < 0.5 else [])
    found = _person(f"{pair}-F", "found", pair_id=pair, should_match=1, name=_perturb_name(b["name"]),
                    gender=b["gender"], age_band=found_age, languages=b["languages"],
                    clothing=shared, features=b["features"], location=b["location"],
                    centre=centres[1], created=t0 + timedelta(hours=RNG.randint(1, 6)))
    return [lost, found]


def make_negative(i: int) -> list[Person]:
    b = _base()
    t0 = datetime(2027, 7, 29, RNG.randint(5, 20), tzinfo=timezone.utc)
    centres = RNG.sample(_CENTRES, 2)
    pair = f"neg-{i:03d}"
    lost = _person(f"{pair}-L", "lost", pair_id=pair, should_match=0, name=b["name"],
                   gender=b["gender"], age_band=b["age_band"], languages=b["languages"],
                   clothing=b["clothing"], features=b["features"], location=b["location"],
                   centre=centres[0], created=t0)
    # different person: same gender+age (confusable) but different name/lang/location/clothing
    other_name = f"{RNG.choice(_FIRST)} {RNG.choice(_LAST)}"
    while other_name.split()[0] == b["name"].split()[0]:
        other_name = f"{RNG.choice(_FIRST)} {RNG.choice(_LAST)}"
    other_lang = [RNG.choice([x for x in _LANGS if x not in b["languages"]])]
    other_loc = RNG.choice([x for x in _LOCATIONS if x != b["location"]])
    found = _person(f"{pair}-F", "found", pair_id=pair, should_match=0, name=other_name,
                    gender=b["gender"], age_band=b["age_band"], languages=other_lang,
                    clothing=RNG.sample(_CLOTHES, 2), features=[], location=other_loc,
                    centre=centres[1], created=t0 + timedelta(hours=RNG.randint(1, 6)))
    return [lost, found]


def main() -> None:
    n_pos = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    n_neg = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    init_db()
    removed = repo.clear_test_pairs()
    persons: list[Person] = []
    for i in range(n_pos):
        persons += make_positive(i)
    for i in range(n_neg):
        persons += make_negative(i)
    repo.insert_many(persons)
    # test_pair_id/should_match aren't Person fields; stamp the columns from the id pattern.
    _stamp_pair_columns(persons)
    print(f"Cleared {removed} old test rows. Inserted {n_pos} positive + {n_neg} negative pairs "
          f"({len(persons)} records).")


def _stamp_pair_columns(persons: list[Person]) -> None:
    conn = repo.get_conn()
    for p in persons:
        pair = p.id.rsplit("-", 1)[0]
        should = 1 if pair.startswith("pos-") else 0
        conn.execute("UPDATE persons SET test_pair_id=?, test_should_match=? WHERE id=?",
                     (pair, should, p.id))
    conn.commit()


if __name__ == "__main__":
    main()
