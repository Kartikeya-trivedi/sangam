"""Geography primitives for the Nashik-Trimbakeshwar Kumbh (spec §11, §13; DATA.md).

Pure stdlib (csv + xml.etree + math) — no external deps, loads lazily and caches. Reads the
datasets in data/: police stations (CSV), chokepoints with risk (KML), zone centroids (CSV).
Powers the ops map, hotspot prediction, nearest-help routing, and the navigation agent
(services/nav_agent.py). Owned by Role 1 (ROLES.md) so ops.py stays Role 2's.
"""
from __future__ import annotations

import csv
import math
import pathlib
import re
import xml.etree.ElementTree as ET
from functools import lru_cache

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
_KML_NS = {"k": "http://www.opengis.net/kml/2.2"}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _field(desc: str, key: str) -> str:
    m = re.search(rf"{key}:\s*([^|]+)", desc or "")
    return m.group(1).strip() if m else ""


@lru_cache(maxsize=1)
def police_stations() -> list[dict]:
    out: list[dict] = []
    p = DATA / "Police_Stations.csv"
    if not p.exists():
        return out
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                out.append({"name": r["station_name"].strip(), "lat": float(r["latitude"]), "lng": float(r["longitude"])})
            except (KeyError, ValueError):
                continue
    return out


@lru_cache(maxsize=1)
def chokepoints() -> list[dict]:
    """Chokepoints/parking/transfer nodes WITH risk + category (from the richer KML)."""
    out: list[dict] = []
    p = DATA / "Chokepoints_Parking.kml"
    if not p.exists():
        return out
    for pm in ET.parse(p).getroot().iterfind(".//k:Placemark", _KML_NS):
        coord = (pm.findtext(".//k:coordinates", default="", namespaces=_KML_NS) or "").strip()
        if not coord:
            continue
        lng, lat = (float(x) for x in coord.split(",")[:2])
        desc = pm.findtext("k:description", default="", namespaces=_KML_NS) or ""
        out.append(
            {
                "name": (pm.findtext("k:name", default="", namespaces=_KML_NS) or "").strip(),
                "category": _field(desc, "Category"),
                "risk": _field(desc, "Risk"),
                "lat": lat,
                "lng": lng,
            }
        )
    return out


@lru_cache(maxsize=1)
def zones() -> list[dict]:
    out: list[dict] = []
    p = DATA / "Zone_Boundaries.csv"
    if not p.exists():
        return out
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                out.append({"name": r["zone_name"].strip(), "lat": float(r["centroid_lat"]), "lng": float(r["centroid_lng"])})
            except (KeyError, ValueError):
                continue
    return out


def _nearest(lat: float, lng: float, items: list[dict]) -> dict | None:
    if not items:
        return None
    best = min(items, key=lambda it: haversine_km(lat, lng, it["lat"], it["lng"]))
    return {**best, "distance_km": round(haversine_km(lat, lng, best["lat"], best["lng"]), 2)}


def nearest_police_station(lat: float, lng: float) -> dict | None:
    return _nearest(lat, lng, police_stations())


def nearest_help_point(lat: float, lng: float) -> dict | None:
    """Nearest help-desk candidate — transfer nodes & chokepoints are natural placements."""
    cands = [c for c in chokepoints() if c["category"] in ("Transfer node", "Traffic choke point", "No-vehicle pressure zone")]
    return _nearest(lat, lng, cands or chokepoints())


def locate_zone(lat: float, lng: float) -> dict | None:
    return _nearest(lat, lng, zones())


def list_hotspots() -> list[dict]:
    """The very-high-risk points where separations cluster (DATA.md)."""
    return [c for c in chokepoints() if c["risk"].lower() == "very high"]


def geocode_location(name: str) -> dict | None:
    """Resolve a known landmark/zone/station name to coordinates (substring match)."""
    q = (name or "").strip().lower()
    if not q:
        return None
    for pool in (chokepoints(), zones(), police_stations()):
        for it in pool:
            n = it["name"].lower()
            if q in n or n in q:
                return {"name": it["name"], "lat": it["lat"], "lng": it["lng"]}
    return None
