"""Domain constants grounded in the dataset analysis (single source of truth).

Age bands match the synthetic dataset EXACTLY so seeded records, Claude extraction, and the
matching engine all speak the same vocabulary. Centre IDs are slugs of the 10 real centre
names that appear in Synthetic_Missing_Persons_2500.csv.
"""
from __future__ import annotations

# --- Age bands (ordered youngest -> oldest; "unknown" is off-scale) ---
AGE_BANDS: tuple[str, ...] = ("0-12", "13-17", "18-40", "41-60", "61-70", "71-80", "80+")
AGE_BAND_INDEX: dict[str, int] = {b: i for i, b in enumerate(AGE_BANDS)}
MINOR_BANDS: frozenset[str] = frozenset({"0-12", "13-17"})


def is_minor_band(age_band: str) -> bool:
    return age_band in MINOR_BANDS


def age_band_distance(a: str, b: str) -> int | None:
    """Ordinal distance between two bands; None if either is unknown/off-scale."""
    if a not in AGE_BAND_INDEX or b not in AGE_BAND_INDEX:
        return None
    return abs(AGE_BAND_INDEX[a] - AGE_BAND_INDEX[b])


# --- The 10 reporting centres (name -> slug). Counts are the dataset case totals. ---
CENTRES: dict[str, str] = {
    "Adgaon Kho-Ya-Paya": "adgaon_kho_ya_paya",
    "Rajur Bahula Center": "rajur_bahula_center",
    "Panchavati Center": "panchavati_center",
    "Ramkund Kho-Ya-Paya Kendra": "ramkund_kho_ya_paya_kendra",
    "Bharat Bharati Control Room": "bharat_bharati_control_room",
    "Trimbakeshwar Kho-Ya-Paya Kendra": "trimbakeshwar_kho_ya_paya_kendra",
    "Central Control Room": "central_control_room",
    "Nashik Road Center": "nashik_road_center",
    "Sadhugram Lost Found": "sadhugram_lost_found",
    "Police Main Control Room": "police_main_control_room",
}
CENTRE_SLUGS: frozenset[str] = frozenset(CENTRES.values())
SLUG_TO_NAME: dict[str, str] = {v: k for k, v in CENTRES.items()}


def slugify_centre(name: str) -> str:
    """Map a raw centre name to its canonical slug (idempotent for slugs already)."""
    if name in CENTRE_SLUGS:
        return name
    if name in CENTRES:
        return CENTRES[name]
    return name.strip().lower().replace("-", " ").replace("/", " ").replace("  ", " ").replace(" ", "_")


# Canonical language vocabulary (lowercase English) seen in / expected from the data.
LANGUAGES: tuple[str, ...] = (
    "hindi", "bengali", "kannada", "maithili", "gujarati", "telugu", "bhojpuri",
    "awadhi", "tamil", "marathi", "malayalam", "punjabi", "urdu", "odia", "assamese",
)
