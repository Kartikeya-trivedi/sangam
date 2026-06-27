# SETU · सेतु — Missing-Persons Reunification for the Kumbh Mela

> **A bridge between the lost and their family.** A family describes a missing relative **by
> voice, in any of 9 Indian languages** (or a photo, or a few taps); SETU matches them against
> everyone logged "found" across **every** lost-and-found centre using **cross-language + cross-modal
> AI**, returns a ranked, *explained* candidate list, and an agentic dispatcher actively works the
> case until they're reunited.

Built for the **Claude Impact Lab** for the **Nashik–Trimbakeshwar Simhastha Kumbh Mela 2027**
(~80 million pilgrims, ~28 km of ghats, intermittent connectivity, mostly low-literacy and
multilingual). The hard problem isn't a database — it's understanding a panicked, code-mixed
description and matching it across a chaotic, photo-less, multi-centre reality.

📖 **Visual explainer:** open [`docs/how-it-works.html`](docs/how-it-works.html) in a browser.

---

## ✨ What makes SETU different

| | Feature | Why it matters |
|---|---|---|
| 🖼️ | **Cross-modal matching (VLM)** | The dataset has *no photos*, so face-recognition can't match a family's snapshot against text records. **Claude Vision** converts a photo into the *same canonical attributes* the records use — so a photo of grandpa matches a text-logged "elderly man, blue kurta, walking stick." |
| 🤖 | **Sahayak — agentic dispatcher** | Doesn't just search. For each case Claude reasons step-by-step **live on the map**: reads → scans every centre → **predicts the drift-zone from real Kumbh crowd geography** (ghats, chokepoints) → dispatches a localized loudspeaker announcement → notifies the family. |
| 🌐 | **Truly multilingual, voice-first** | 9 Indian languages end-to-end — UI, spoken readback (TTS), and **cross-language matching** (a Hindi report matches a person logged in Tamil). |
| 🔍 | **Explainable matching** | Never a black-box yes/no — ranked top-K candidates each with a plain-language *"why it matched"* a volunteer can act on. |
| 🛡️ | **Child-safety first (§12)** | Minors are **never publicly announced** — a minor triggers a private staff alert + guardian verification. No names/phones in logs or URLs. |
| 📴 | **Offline-resilient** | Every external service (Claude, Sarvam, faces) degrades gracefully — the app **boots, seeds, and matches with zero API keys**, so the camp never goes fully down. |

---

## 🧭 The reunification journey

```
1. REPORT      Pilgrim PWA · voice / photo / taps · 9 languages · no login
       ↓
2. UNDERSTAND  Sarvam STT → Claude normalises to canonical English
               Claude Vision reads the photo into the same vocabulary (cross-modal)
       ↓
3. MATCH       face + attribute + geo scoring across every centre
               → ranked top-K, re-ranked + explained by Claude
       ↓
4. SAHAYAK     agentic dispatcher: predict drift-zone → announce to the right desks → re-check
       ↓
5. REUNITE     call the family · child-safety gate for minors · everything audit-logged
```

---

## 🏗️ Architecture

A **graceful-degradation FastAPI monolith** + two **React/Vite** frontends.

```
┌── frontend/pilgrim ──┐   ┌── frontend/ops ───────┐
│ Voice-first PWA      │   │ Officials dashboard    │
│ (kiosk, 9 langs)     │   │ Sahayak · Google Map · │
│ language→triage→     │   │ case queue · confirm   │
│ report | I-am-lost   │   │ reunions               │
└──────────┬───────────┘   └───────────┬────────────┘
           └──────────────┬────────────┘
                          ▼  REST  /api/v1/*
              ┌──────────────────────────────┐
              │  FastAPI backend (SQLite)     │
              │  intake · match · announce ·  │
              │  ops · sahayak (SSE)          │
              └──────────────┬───────────────┘
   ┌──────────────┬──────────┼───────────┬──────────────┐
   ▼              ▼          ▼            ▼              ▼
🧠 Claude     🗣️ Sarvam   😶 InsightFace 🗃️ SQLite+FTS  🗺️ Google Maps
reasoning+    STT(Saarika) face          person         ops basemap
vision        TTS(Bulbul)  embeddings    registry
```

### Repo layout
```
backend/    FastAPI — routers (intake/match/announce/ops/dispatcher),
            services (claude, vision, speech, faces, matching, geo, dispatcher), db (SQLite)
frontend/
  pilgrim/  voice-first PWA — screens (Language, Intent triage, Report, SelfLost),
            components (MatchResults, NearbyDesks, ChipGroup, SpeakHint), i18n (9 langs)
  ops/      dashboard — Sahayak (live agent), MapView (Google Maps), CaseQueue, MatchDrawer
scripts/    seed_e2e.py · seed_dataset.py · locate.py (crowd-scan & mark)
e2e/        Playwright — full-stack offline suite (api · pilgrim · ops)
docs/       how-it-works.html · E2E_GUIDE · INFRA · MAP
data/       Kumbh datasets (KMLs, chokepoints, zones, synthetic persons)
```

---

## 🚀 Quick start

**Prereqs:** [uv](https://docs.astral.sh/uv/) (Python) · Node 20+ · (optional) Docker.

```bash
# 1. Backend — boots and matches with NO keys
cd backend
uv sync
uv run python ../scripts/seed_e2e.py        # deterministic demo data (incl. a minor)
uv run uvicorn main:app --reload --port 8000 # API docs → http://localhost:8000/docs

# 2. Frontends (each in its own shell)
cd frontend/pilgrim && npm install && npm run dev   # http://localhost:5173
cd frontend/ops     && npm install && npm run dev   # http://localhost:5174
```

Open the **pilgrim app** (`:5173`) to report/triage, and the **ops dashboard** (`:5174`) →
**🤖 Sahayak** tab to watch the agent work a case live on the map.

---

## 🔑 Environment variables

**Required to run / demo: NONE.** The whole stack boots and matches offline. Keys only upgrade
quality. Put them in `backend/.env` (gitignored — never commit, never `export` in your shell):

| Var | Where | Effect when unset |
|---|---|---|
| `ANTHROPIC_API_KEY` | platform.claude.com → `backend/.env` | Naive keyword extractor instead of real Claude reasoning/vision/rerank |
| `SARVAM_API_KEY` | dashboard.sarvam.ai → `backend/.env` | Typed/tap path + browser TTS instead of Sarvam voice (Saarika STT / Bulbul TTS) |
| `VITE_GOOGLE_MAPS_API_KEY` | `frontend/ops/.env` | Ops map needs this for the live Google basemap |
| `ANTHROPIC_MODEL` · `VITE_API_BASE` · `VITE_CENTRE_ID` · `OFFLINE_MODE` · `TTL_DAYS` | optional | Sensible defaults (`claude-haiku-4-5`, `http://localhost:8000`, `central_control_room`, …) |

> ⚠️ Google Maps JS keys are **public by design** (baked into the client bundle) — protect them
> with HTTP-referrer + API restrictions in the Google Cloud Console, not by secrecy.

---

## 🔌 Key API endpoints (`/api/v1`)

| Method · Path | Purpose |
|---|---|
| `GET /health` | Liveness + which capabilities (claude/sarvam/insightface) are detected |
| `GET /api/v1/centres` | The 10 lost-and-found centres + coords (for nearby-desk lookup) |
| `POST /api/v1/report/lost` · `/found` | Intake (multipart: text/audio/photo/taps) → structured profile + ranked candidates |
| `GET /api/v1/match/{report_id}` | Re-run matching for an existing report |
| `POST /api/v1/announce` · `/speak` | Reunification announcement / UI TTS (minors blocked → 403 + guardian path) |
| `GET /api/v1/ops/cases` · `/map` · `/stats` | Dashboard queue, GeoJSON map layers, stats |
| `POST /api/v1/ops/confirm` · `/reject` | Confirm / reject a reunion |
| `GET /api/v1/ops/dispatch/{id}/stream` | **Sahayak** — Server-Sent Events of the agent's reasoning steps, live |

---

## 🧪 Testing

A full-stack **Playwright** suite that boots the backend + both frontends itself and runs
entirely offline (no keys, deterministic):

```bash
cd e2e && npm install && npx playwright install chromium && npm test
```

Covers: offline `/health`, text+tap & photo reports, **cross-modal VLM**, child-safety announce
block, the ops queue + Google map, and the pilgrim triage → report happy path.
Backend unit tests: `cd backend && uv run pytest -q` (+ `uv run ruff check .`).

---

## 🎨 Design

The pilgrim app uses **"Tirth"** — a warm mela-wayfinding aesthetic (parchment + marigold/saffron +
kumkum vermillion + indigo ink + gold, Baloo 2 + Noto Serif Devanagari), built for sunlight,
shaky hands, and low literacy: huge tap targets, the app talks back, one action per screen.

---

## 🧰 Tech stack

**Backend** FastAPI · Pydantic · SQLite (FTS) · RapidFuzz · NumPy · Anthropic SDK · SarvamAI · InsightFace (optional)
**Frontend** React 18 · Vite · TypeScript · Google Maps JS · MapLibre (legacy) · PWA
**AI** Claude (extraction · vision · rerank · announce · Sahayak) · Sarvam (STT/TTS) · InsightFace (face embeddings)

---

*SETU · सेतु — a bridge between the lost and their family.*
