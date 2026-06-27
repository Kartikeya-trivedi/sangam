# SETU — End-to-End tests (Playwright)

Full-stack E2E across the real **backend + pilgrim PWA + ops dashboard**. Everything runs
**offline with zero API keys** — SETU degrades gracefully by design, so the suite needs no
secrets to pass.

## What it does

Playwright boots the whole stack itself (`webServer` in `playwright.config.ts`):

| Service | Command | URL |
|---|---|---|
| Backend (FastAPI) | `uv run uvicorn main:app --port 8000` | http://localhost:8000 |
| Pilgrim PWA (Vite) | `npm run dev -- --port 5173` | http://localhost:5173 |
| Ops dashboard (Vite) | `npm run dev -- --port 5174` | http://localhost:5174 |

`global-setup.ts` seeds deterministic FOUND people (incl. one minor) via
[`scripts/seed_e2e.py`](../scripts/seed_e2e.py) before the run.

## Run it

```bash
# one-time
cd e2e
npm install
npx playwright install chromium

# run
npm test                 # headless
npm run test:headed      # watch it drive the browser
npm run report           # open the HTML report
```

Already have the servers running? They're reused automatically (`reuseExistingServer`).

## Coverage

- **`api.spec.ts`** — offline `/health`; `report/lost` via text+taps returns a ranked match
  against the seed; **taps-only** report succeeds (no `no_input`); missing `centre_id` → 422;
  minor announce is **blocked** (child-safety §12); `ops/cases` + `ops/map` healthy.
- **`pilgrim.spec.ts`** — pick language → tap gender/age/place → enter phone → submit →
  success screen with a case id; submit disabled until a callback number is entered.
- **`ops.spec.ts`** — dashboard loads the seeded case queue; map legend renders; a minor case
  surfaces in the derived private staff-alerts panel.

## Required env

**None.** The stack boots and the suite passes with no keys. Optional keys only upgrade the
*live* experience (real Claude extraction, Sarvam voice, street basemap) — see the repo
`.env.example` and `docs/E2E_GUIDE.md`.
