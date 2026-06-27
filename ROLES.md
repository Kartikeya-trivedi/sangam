# SETU — Team Roles & Parallel Workstreams

Goal: **4 people build in parallel with near-zero merge conflicts.** The rule that makes that
work: *you only edit files inside your owned paths.* The few cross-cutting files have a single
owner and are frozen early.

Branch per role; PR into `main`; never push to `main` directly.

---

## Role 1 — Matching & Data Intelligence
**Branch:** `feat/matching-and-data`  ·  *Suggested: Kartikeya / strongest Python dev*

**Owns**
- `backend/services/matching.py`
- `backend/services/claude.py`
- `backend/services/geo.py`  *(NEW — keep geo logic here so nobody else edits `ops.py`)*
- `backend/db/**` (`faiss_index.py`, `supabase_client.py`, `schema.sql`)
- `scripts/**` (`load_dataset.py`, `eval_dedup.py`, `seed_found_persons.py`)
- `data/**` (read-only)

**First tasks**
1. `load_dataset.py` — ingest `data/Synthetic_Missing_Persons_2500.csv` into the registry.
2. `eval_dedup.py` — score the matcher vs `is_duplicate_report` → **precision / recall / F1** (the killer demo metric).
3. Add dataset signals **on top of** face matching (keep face!): fuzzy name, language, district/state, age/gender, Claude-normalized description. Face still dominates when a photo exists.
4. `geo.py`: `last_seen_location` → lat/lng; real-distance `geo_proximity` from `data/*.csv`.

---

## Role 2 — Backend API, Speech, Safety & Contracts
**Branch:** `feat/backend-api-integrations`  ·  *Suggested: integration lead*

**Owns**
- `backend/main.py`, `backend/config.py`
- `backend/models.py`  ← **the shared contract. Single owner. Freeze v1 in the first 30 min.**
- `backend/routers/**` (intake, match, announce, ops)
- `backend/services/speech.py` (Sarvam), `backend/services/faces.py` (InsightFace)
- `backend/safety.py`
- `Dockerfile`, `docker-compose.yml`, `pyproject.toml`  ← **backend dependency owner**

**First tasks**
- Wire Sarvam Saaras/Bulbul + real Claude calls; finalize endpoints; child-safety; deploy.
- Routers call matching/geo via **stable function signatures** agreed with Role 1.
- Any `models.py` change → announce it in chat; others rebase immediately.

---

## Role 3 — Pilgrim App + Android (Capacitor)
**Branch:** `feat/pilgrim-android`  ·  *Suggested: frontend/mobile dev*

**Owns:** `frontend/pilgrim/**` (only)

**First tasks**
- Modernize the 5 screens (Tailwind), wrap with **Capacitor → Android APK**, hold the §2 voice-first UX laws.
- Talk to the backend **only** through `frontend/pilgrim/api.ts`.

---

## Role 4 — Ops Dashboard + Maps/Geo
**Branch:** `feat/ops-dashboard-maps`  ·  *Suggested: data-viz dev*

**Owns:** `frontend/ops/**` (only)

**First tasks**
- MapLibre layers from `data/` (CCTV, zones, police, chokepoints) + **hotspot heat**; case queue + match review.
- **Switch the map center to Nashik–Trimbakeshwar** (~19.99 N, 73.79 E).
- Talk to the backend **only** through `frontend/ops/api.ts`.

---

## Why this avoids conflicts
- Each role edits a **disjoint directory tree**. The two frontends have separate `api.ts` files.
- The only cross-cutting files — `models.py`, `main.py`, `pyproject.toml`, `ops.py` — are **all owned by Role 2**. Role 1 keeps geo logic in its own `geo.py`, so two people never edit `ops.py`.
- Backend ↔ frontend coupling is the JSON contract in `models.py` (Role 2). Freeze it first; treat changes like an API version bump.

## Workflow
- `git checkout <your branch>` → work → PR into `main`.
- `git pull --rebase origin main` at the start of every work block.
- Keep PRs small and inside your owned paths.

## "Dataset on top, not instead of"
The provided dataset has **no photos**, so we **keep the full SETU solution** (voice intake, Claude
normalization, InsightFace face matching, announcements) and **add** the dataset as: (a) the seed for
the registry at 2,500-record scale, (b) extra matching signals + a measurable dedup eval, (c) the
geography for the map/hotspots. Face matching stays the primary signal whenever a live photo is
captured. See [DATA.md](DATA.md).
