# SETU — Missing-Persons Reunification (Kumbh Mela 2027)

> A bridge between the lost and their family. Voice-first, cross-language, face + attribute
> matching across every lost-and-found centre — replacing "broadcast a name and hope."

> **Team:** see [ROLES.md](ROLES.md) for the 4-person, zero-conflict split. **Datasets:** see [DATA.md](DATA.md).

This is the **initial scaffold** built to `SETU_BUILD_SPEC.md`. The structure, data model,
API surface, matching engine, and both frontends are in place. Cloud integrations (Sarvam STT/TTS,
Claude, Supabase) are stubbed behind graceful fallbacks so the app **boots and demos offline today**,
then lights up as you drop in keys.

## Quick start

```bash
# 1. Backend (uv — https://docs.astral.sh/uv/)
cp .env.example .env            # fill keys later; works without them
cd backend
uv sync                         # core deps; app boots (face matching degrades, §13)
#   uv sync --extra faces       # on the A6000 GPU box: adds InsightFace + onnxruntime-gpu
uv run uvicorn main:app --reload --port 8000     # docs at http://localhost:8000/docs

# 2. Seed demo "found" people (in another shell, backend running)
uv run python ../scripts/seed_found_persons.py

# 3. Frontends (each in its own shell)
cd frontend/pilgrim && npm install && npm run dev      # http://localhost:5173
cd frontend/ops     && npm install && npm run dev      # http://localhost:5174

# Or everything at once:
docker compose up
```

Try it with no keys: `POST /report/lost` with `text="buzurg aadmi, blue kurta, Tamil bolte hain"`
returns a structured profile + ranked candidates against the seeded found-persons.

## What runs today (offline, no keys)

- Full intake pipeline with the **typed-text** path and a **naive keyword extractor** standing in for Claude.
- **Matching engine** (`services/matching.py`) — real face + attribute + geo scoring, top-K with breakdown.
- **Local store** (`db/faiss_index.py`) — in-memory, brute-force cosine; the offline/edge path (§13).
- **Child-safety branch** (`safety.py`) — minors blocked from public announce, private staff alert + audit.
- **Pilgrim PWA** — 5 linear voice-first screens; TTS falls back to the browser's speech synthesis.
- **Ops dashboard** — MapLibre case map + case queue + staff alerts.

## What to wire next (marked `TODO` in code)

| Area | File | Swap the fallback for… |
|---|---|---|
| STT / TTS | `backend/services/speech.py` | Sarvam Saaras + Bulbul v3 |
| Reasoning | `backend/services/claude.py` | Real Claude extract / rerank / announce calls |
| Faces | `backend/services/faces.py` | InsightFace `buffalo_l` on the A6000 (loads when installed) |
| Central store | `backend/db/supabase_client.py` | Supabase inserts + pgvector `<=>` search |

## Layout

```
backend/    FastAPI monolith — routers (§7), services (§4), db (§6), safety (§12)
frontend/   pilgrim/ PWA kiosk (§2 UX laws) + ops/ dashboard (§11)
scripts/    seed_found_persons.py (§15 demo data)
```

## Build order (spec §15)

Phase 0 setup ✅ scaffold → Phase 1 core matching path → Phase 2 pilgrim happy path →
Phase 3 ops dashboard → Phase 4 differentiators (minor safety / offline / announce TTS) →
Phase 5 polish + demo rehearsal (§16). Never cut: voice-first happy path, messy-data demo, child-safety branch.
