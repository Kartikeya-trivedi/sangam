# CLAUDE.md

Guidance for Claude Code (and any AI agent) working in this repo. Read this first.

## What this is
**SETU** — a missing-persons reunification system for the **Nashik–Trimbakeshwar Simhastha Kumbh
Mela 2027** (~80M pilgrims). A family describes a lost relative **by voice in any Indian language**
(+ optional photo); SETU matches against people logged "found" across **every** lost-and-found
center using **face + attribute + geo matching with cross-language normalization**, returns a
ranked, *explained* candidate list, and triggers a reunification announcement.

Built for the Claude Impact Lab hackathon (Mumbai). Sources of truth:
- [SETU_BUILD_SPEC.md](SETU_BUILD_SPEC.md) — the full spec (UX laws §2, rubric §3, safety §12, offline §13).
- [DATA.md](DATA.md) — datasets + how to use them. [flow.md](flow.md) — end-to-end flows.
- [ROLES.md](ROLES.md) — the 4-person, zero-conflict workstream split.

## Architecture
Python **FastAPI monolith** (`backend/`) + two **React/Vite** frontends:
`frontend/pilgrim` (voice-first PWA, wrapped with **Capacitor** for Android) and
`frontend/ops` (**MapLibre** dashboard). **Claude** = reasoning; **Sarvam** = speech only;
**InsightFace** = face embeddings; **pgvector** (central) + **FAISS** (offline edge) = vector store.

## Commands
Backend (uv — package manager):
```bash
cd backend
uv sync                  # core deps; add --extra faces on a GPU box (InsightFace + onnxruntime-gpu)
uv run uvicorn main:app --reload --port 8000     # API docs at /docs
uv run python ../scripts/seed_found_persons.py   # toy seed (use load_dataset.py for the real set)
uv run ruff check .      # lint
```
Frontends:
```bash
cd frontend/pilgrim && npm install && npm run dev   # http://localhost:5173
cd frontend/ops     && npm install && npm run dev   # http://localhost:5174
```
Everything at once: `docker compose up`.

## Layout & ownership
```
backend/
  main.py · config.py · models.py      # app, settings, the Person CONTRACT
  routers/{intake,match,announce,ops}.py
  services/{claude,speech,faces,matching}.py   (+ geo.py to add)
  db/{faiss_index,supabase_client,schema.sql}
  safety.py                             # child-safety + audit log
frontend/pilgrim/**   frontend/ops/**
scripts/**   data/**
```
`models.py` is the **shared contract** between backend and both frontends — single owner (Role 2),
freeze v1 early. See ROLES.md for who owns what; **stay inside your owned paths and PR into `main`.**

## Conventions & patterns — follow the existing code
- **Graceful degradation everywhere.** Every external service (Sarvam, Claude, InsightFace,
  Supabase) has a no-key / offline fallback and the app must still boot and match. Mirror the
  pattern in `services/*.py` (lazy client; return `None`/mock when unconfigured). Never hard-crash
  on a missing key — the camp must never go fully down (§13).
- **Claude calls:** strict JSON, "return ONLY JSON", parse defensively (strip code fences). One
  reused extraction prompt, one rerank, one announce. Matching fields are **canonical English**;
  `native_summary` stays in the reporter's language/script.
- **Bulbul TTS needs native script**, never romanized.
- **Matching is never a hard binary** — always ranked top-K with a score breakdown + explanation.
- **Child safety is non-negotiable (§12):** `is_minor` ⟶ never a public announce; create a private
  staff alert + guardian-verification task; audit every confirm/announce; **no PII (names/phones)
  in logs or URLs**; prefer storing embeddings over raw photos; TTL auto-purge.
- **Pilgrim UX laws (§2):** voice-first; the app talks back (auto-TTS on every screen); one action
  per screen; huge buttons; no login. Route all pilgrim UI through `BigButton` + `SpeakHint` +
  `useSpeak`. (The ops dashboard is a normal data-dense app, exempt.)
- Python: type hints, `from __future__ import annotations`, ruff line-length 110.

## Domain facts that change decisions
- **Venue is Nashik–Trimbakeshwar (~19.99 N, 73.79 E), not Prayagraj.** Some scaffold demo coords
  still say Prayagraj — fix them to Nashik.
- **The provided dataset has no photos.** Against it, the hero feature is **cross-center
  attribute/text dedup**, evaluated with the `is_duplicate_report` ground truth (~8%). Face matching
  stays a *live-intake* feature. Keep both — "dataset on top, not instead of".
- **Hotspots** = the 6 *very-high*-risk chokepoints + 3 no-vehicle pressure zones (Ramkund /
  Godavari ghats) in `data/Chokepoints_Parking.kml`. Weight geo by risk; place help-desks there.
- Geo data: prefer the **KMLs** (risk levels, real zone polygons, ~4,100 cameras) over the thinner CSVs. See DATA.md.

## Gotchas
- **Do NOT set `ANTHROPIC_API_KEY` in your shell** — it's app-side only (`backend/.env`); keep
  Claude Code on the Max plan, or it bills the API account.
- `onnxruntime-gpu` needs CUDA; on a CPU box swap to `onnxruntime` (uv extra `faces`).
- `.env` is gitignored — never commit keys. `.env.example` documents the vars.
- Run `uvicorn` **from `backend/`** — imports are package-relative (`from config import ...`,
  `from services import ...`).

## Before you call it done
- Backend: `uv run ruff check .` and confirm the app boots (`GET /health`).
- **Test with no keys set** — don't break the offline/degraded path.
- Keep changes inside your role's owned paths; small PRs into `main`.
