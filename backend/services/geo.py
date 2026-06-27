"""Geo signals: landmark -> coordinate lookup, proximity scoring, and dataset map layers.

The synthetic data names 20 `last_seen_location` landmarks and 10 centres but gives them no
coordinates, so we curate an approximate Nashik-Trimbakeshwar gazetteer here (real venue is
~19.99 N, 73.79 E; Trimbakeshwar ~28 km west at ~19.93 N, 73.53 E). Coordinates are approximate
but geographically sensible — matching only needs *relative* proximity.

Zone centroids, police stations and chokepoints are read from data/*.csv (stdlib csv, no pandas)
for the ops map + nearest-help-point routing.
"""
from __future__ import annotations

import csv
import math
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# --- curated gazetteer: last_seen_location -> (lat, lng) ----------------------------------
LANDMARKS: dict[str, tuple[float, float]] = {
    "ramkund ghat": (19.9993, 73.7906),
    "kushavart kund": (19.9337, 73.5300),
    "trimbakeshwar approach": (19.9400, 73.5400),
    "trimbak road": (19.9600, 73.6500),
    "panchavati circle": (20.0070, 73.7950),
    "laxmi narayan ghat": (20.0010, 73.7920),
    "nandur ghat": (20.0200, 73.8300),
    "dasak ghat": (19.9600, 73.8400),
    "takli sangam": (19.9200, 73.8000),
    "kapila sangam": (20.0300, 73.8000),
    "gauri patangan": (19.9900, 73.7800),
    "madsangvi transit": (20.0200, 73.8200),
    "sadhugram gate 1": (20.0150, 73.8150),
    "sadhugram gate 2": (20.0160, 73.8160),
    "adgaon parking": (20.0150, 73.8270),
    "nashik road station": (19.9476, 73.8401),
    "bus stand nashik": (19.9975, 73.7768),
    "main police chowki": (19.9970, 73.7890),
    "dindori road crossing": (20.0300, 73.7800),
    "rajur bahula": (20.0500, 73.7200),
}

# --- centre slug -> approximate coordinate -------------------------------------------------
CENTRE_COORDS: dict[str, tuple[float, float]] = {
    "ramkund_kho_ya_paya_kendra": (19.9993, 73.7906),
    "panchavati_center": (20.0070, 73.7950),
    "trimbakeshwar_kho_ya_paya_kendra": (19.9340, 73.5300),
    "nashik_road_center": (19.9476, 73.8401),
    "adgaon_kho_ya_paya": (20.0150, 73.8270),
    "sadhugram_lost_found": (20.0150, 73.8150),
    "police_main_control_room": (19.9970, 73.7890),
    "central_control_room": (19.9980, 73.7900),
    "bharat_bharati_control_room": (20.0000, 73.7800),
    "rajur_bahula_center": (20.0500, 73.7200),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def location_to_coords(name: str | None) -> tuple[float, float] | None:
    if not name:
        return None
    return LANDMARKS.get(name.strip().lower())


def _dist_to_score(km: float) -> float:
    """Bucketed proximity score (PRD §4): closer -> higher."""
    if km < 1.0:
        return 0.95
    if km < 3.0:
        return 0.75
    if km < 8.0:
        return 0.5
    if km < 20.0:
        return 0.3
    return 0.15


def geo_proximity(q_loc: str | None, c_loc: str | None) -> tuple[float, bool]:
    """Score 0..1 from two last_seen_location names; bool = whether the signal was usable.

    Same name -> 1.0. Both geocoded -> distance bucket. Otherwise neutral 0.5 (not a penalty).
    """
    ql = (q_loc or "").strip().lower()
    cl = (c_loc or "").strip().lower()
    if not ql or not cl:
        return 0.5, False
    if ql == cl:
        return 1.0, True
    qc, cc = LANDMARKS.get(ql), LANDMARKS.get(cl)
    if qc and cc:
        return _dist_to_score(haversine_km(*qc, *cc)), True
    # both present but unknown to gazetteer: token overlap, weak
    return (0.6 if set(ql.split()) & set(cl.split()) else 0.25), True


def centre_proximity(q_centre: str | None, c_centre: str | None) -> tuple[float, bool]:
    """Score 0..1 from two centre slugs. Same centre -> 1.0; else distance bucket; unknown -> neutral."""
    if not q_centre or not c_centre:
        return 0.5, False
    if q_centre == c_centre:
        return 1.0, True
    qc, cc = CENTRE_COORDS.get(q_centre), CENTRE_COORDS.get(c_centre)
    if qc and cc:
        return _dist_to_score(haversine_km(*qc, *cc)), True
    return 0.4, True


# --- dataset layers (lazy-loaded, cached) for the ops map ----------------------------------
def _read_csv(name: str) -> list[dict]:
    path = _DATA_DIR / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def zones() -> list[dict]:
    out = []
    for r in _read_csv("Zone_Boundaries.csv"):
        try:
            out.append({"zone_name": r["zone_name"], "lat": float(r["centroid_lat"]),
                        "lng": float(r["centroid_lng"]),
                        "boundary_points": int(r.get("approx_boundary_points") or 0)})
        except (ValueError, KeyError):
            continue
    return out


@lru_cache(maxsize=1)
def police_stations() -> list[dict]:
    out = []
    for r in _read_csv("Police_Stations.csv"):
        try:
            out.append({"station_name": r["station_name"], "lat": float(r["latitude"]),
                        "lng": float(r["longitude"])})
        except (ValueError, KeyError):
            continue
    return out


@lru_cache(maxsize=1)
def chokepoints() -> list[dict]:
    out = []
    for r in _read_csv("Chokepoints_Parking.csv"):
        try:
            out.append({"location_name": r["location_name"], "category": r["category"],
                        "lat": float(r["latitude"]), "lng": float(r["longitude"])})
        except (ValueError, KeyError):
            continue
    return out


def nearest_police(lat: float, lng: float) -> dict | None:
    stns = police_stations()
    if not stns:
        return None
    best = min(stns, key=lambda s: haversine_km(lat, lng, s["lat"], s["lng"]))
    return {**best, "km": round(haversine_km(lat, lng, best["lat"], best["lng"]), 2)}


def nearest_zone(lat: float, lng: float) -> str | None:
    zs = zones()
    if not zs:
        return None
    return min(zs, key=lambda z: haversine_km(lat, lng, z["lat"], z["lng"]))["zone_name"]
