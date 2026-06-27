"""Agentic navigation over the Kumbh geography (Anthropic SDK tool-use, spec §4, §11).

A volunteer describes where a found/lost person is; Claude calls geo tools (geocode, nearest
police, nearest help point, zone, hotspots) in a manual agentic loop and returns short,
actionable routing guidance. Degrades to a deterministic heuristic when ANTHROPIC_API_KEY is
absent so the feature still works offline (spec §13). Tools resolve against services/geo.py.
"""
from __future__ import annotations

import json

from config import settings
from services import geo

try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None

_client = None


def _get_client():
    global _client
    if not settings.has_anthropic or Anthropic is None:
        return None
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


SYSTEM = """You are SETU's navigation assistant for the Nashik-Trimbakeshwar Kumbh Mela.
A volunteer tells you where a found or lost person is. Use the tools to resolve place names
to coordinates, find the nearest police station and help point, identify the zone, and (when
relevant) the separation hotspots. Then give a SHORT, actionable answer a volunteer can act on:
where to take the person, the nearest help, and any caution. Coordinates are latitude/longitude
around Nashik (~19.99 N, 73.79 E)."""

TOOLS = [
    {
        "name": "geocode_location",
        "description": "Resolve a known Kumbh landmark/zone/station name (e.g. 'Ramkund') to lat/lng.",
        "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    },
    {
        "name": "nearest_police_station",
        "description": "Nearest police station to a lat/lng.",
        "input_schema": {
            "type": "object",
            "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}},
            "required": ["lat", "lng"],
        },
    },
    {
        "name": "nearest_help_point",
        "description": "Nearest help-desk candidate (transfer node / chokepoint) to a lat/lng.",
        "input_schema": {
            "type": "object",
            "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}},
            "required": ["lat", "lng"],
        },
    },
    {
        "name": "locate_zone",
        "description": "Identify the administrative zone nearest a lat/lng.",
        "input_schema": {
            "type": "object",
            "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}},
            "required": ["lat", "lng"],
        },
    },
    {
        "name": "list_hotspots",
        "description": "List the very-high-risk separation hotspots across the Mela.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _dispatch(name: str, args: dict):
    if name == "geocode_location":
        return geo.geocode_location(args.get("name", ""))
    if name == "nearest_police_station":
        return geo.nearest_police_station(args["lat"], args["lng"])
    if name == "nearest_help_point":
        return geo.nearest_help_point(args["lat"], args["lng"])
    if name == "locate_zone":
        return geo.locate_zone(args["lat"], args["lng"])
    if name == "list_hotspots":
        return geo.list_hotspots()
    return {"error": f"unknown tool {name}"}


def navigate(query: str, max_iters: int = 6) -> dict:
    """Run the agent loop and return {answer, steps}. Falls back to a heuristic with no key."""
    client = _get_client()
    if client is None:
        return _fallback(query)

    messages: list[dict] = [{"role": "user", "content": query}]
    steps: list[dict] = []
    for _ in range(max_iters):
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        if resp.stop_reason != "tool_use":
            answer = "".join(b.text for b in resp.content if b.type == "text")
            return {"answer": answer, "steps": steps}

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                out = _dispatch(b.name, b.input or {})
                steps.append({"tool": b.name, "input": b.input, "output": out})
                results.append(
                    {"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out, default=str)}
                )
        messages.append({"role": "user", "content": results})

    return {"answer": "Could not complete navigation in the step budget.", "steps": steps}


def _fallback(query: str) -> dict:
    """No Claude key: geocode any known landmark in the text, then nearest police + help + zone."""
    ql = (query or "").lower()
    loc = None
    for pool in (geo.chokepoints(), geo.zones()):
        for it in pool:
            if it["name"].lower() in ql:
                loc = {"name": it["name"], "lat": it["lat"], "lng": it["lng"]}
                break
        if loc:
            break
    if not loc:
        return {
            "answer": "Name a known landmark (e.g. Ramkund, Panchavati, Nashik Road) so I can route.",
            "steps": [],
            "hotspots": geo.list_hotspots(),
        }
    pol = geo.nearest_police_station(loc["lat"], loc["lng"])
    hp = geo.nearest_help_point(loc["lat"], loc["lng"])
    zone = geo.locate_zone(loc["lat"], loc["lng"])
    parts = [f"Near {loc['name']}" + (f" ({zone['name']})" if zone else "") + "."]
    if hp:
        parts.append(f"Nearest help point: {hp['name']} ({hp['distance_km']} km).")
    if pol:
        parts.append(f"Nearest police: {pol['name']} ({pol['distance_km']} km).")
    return {"answer": " ".join(parts), "steps": [], "location": loc, "police": pol, "help_point": hp, "zone": zone}
