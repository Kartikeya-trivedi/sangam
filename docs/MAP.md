# SETU — Map Feature & Mock Flow

Pin **where a person was last seen** (lost reports) and **where a found person is now held**
("in our care"), on the Ops dashboard map — privacy-aware, with risk hotspots and police
stations as context. Lives in [ops MapView](../frontend/ops/components/MapView.tsx) +
[`/ops/map` and `/ops/geo`](../backend/routers/ops.py); coordinates resolve via
[`services/geo.py`](../backend/services/geo.py).

## What the map shows
- 🔴 **Last seen (lost)** — pinned at the geocoded `last_seen_location`.
- 🟢 **In our care (found)** — pinned at the centre holding the person.
- 🟩 **Reunited** — case closed.
- 🟣 **Protected (minor)** — redacted pin: generic label only, no name/details (§12).
- 🔵 Police stations · 🔴 soft halos = very-high-risk separation hotspots.

Click any case pin → a popup with the privacy-safe label + status. **No phone numbers or PII
are ever sent to the map** (`/ops/map` builds properties through `_safe_props`).

## Mock flow (no keys needed)
```bash
cd backend && uv run uvicorn main:app --reload          # start backend
uv run python ../scripts/seed_map_demo.py               # seed lost + found + a minor
cd ../frontend/ops && npm install && npm run dev         # open http://localhost:5174 → Map tab
```
You'll see lost pins at Ramkund / Panchavati / Trimbakeshwar, found pins at the holding centres,
and the child case rendered as a **Protected (minor)** purple pin with no identifying details.

## Adding a Maps API key (optional — upgrades the basemap)
The map works on free MapLibre demo tiles out of the box. For a real street basemap, drop a key
into `frontend/ops/.env`:
```
VITE_MAPS_API_KEY=your_maptiler_or_mapbox_key
```
This uses a **MapTiler** street style (MapLibre-native). If your key is a **Google Maps** key,
tell me — Google needs the Google Maps JS SDK (a different component), which I can swap in.
The pinning, privacy, and status logic are independent of the basemap key.

## Privacy & data handling (§12)
- Minors are redacted on the map (no name/summary), distinct color, and never on any public feed.
- Properties carry no phone/PII; only a safe label + status + (optional) centre id.
- Coordinates are jittered slightly so multiple cases at one landmark don't stack.
- Backed by the same TTL auto-purge, consent, and audit rules as the rest of SETU.

## Real geocoding (next step)
`geo.geocode_location` resolves **known landmarks** offline. For arbitrary free-text addresses,
plug a Maps Geocoding API (Google/Mapbox/MapTiler) into a server-side helper and fall back to the
landmark match — a clean drop-in once a key is provided.
