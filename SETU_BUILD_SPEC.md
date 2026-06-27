# SETU — Missing-Persons Reunification System for Kumbh Mela 2027

> **Codename:** SETU (a bridge between the lost and their family). Rename freely.
> **Build context:** One-day hackathon (Claude Impact Lab, Mumbai). ~12 hours, solo/small team. Problem statement = the *bhula-bhatka* (lost-and-found) challenge at Kumbh Mela 2027, ~80M pilgrims.
> **This document is the single source of truth.** Build to this spec. When in doubt, optimize for the judging rubric in §3 and the UX laws in §2 — in that priority order.

---

## 1. Mission & Context

### What we're building
A reunification system that connects pilgrims separated from their families at Kumbh. A relative describes the missing person **by voice in any Indian language** and optionally uploads a photo. The system matches against people logged as "found" at lost-and-found camps across the entire Mela — using **face matching + attribute matching + cross-language normalization** — and produces a ranked, explained list of candidates, then triggers a reunification announcement.

### The system we're improving on (say this to judges)
Today at Kumbh, reunification works like this:
- **Bhula-Bhatka camps** (NGO-run since ~1946): a separated person reaches a camp, and their **name is announced over loudspeakers** along the ghats. The family must happen to *hear* it.
- **Government "Khoya-Paya" / Lost & Found centres** (added 2025): digital registration at each centre, info displayed *at that centre*, PA announcements, and Facebook/Twitter posts.

**The failure modes we kill:**
1. **Name-broadcast-and-hope** — useless if the lost person is a confused elder or child who can't state their name, or if the family never hears the announcement in a 40-crore crowd.
2. **Siloed per centre** — no automatic matching across centres. A family searching at Centre A can't know their person was logged at Centre F.
3. **Monolingual in practice** — a Tamil family and a Hindi loudspeaker don't connect.
4. **Reactive** — the system waits for a human to make the link; it never proactively ranks candidates.

**Positioning:** We *augment* the trusted camp network and honor the government's child-safety protocol. We replace "broadcast a name and hope" with "match a face + description across every centre, in any language."

---

## 2. UX LAWS (HIGHEST PRIORITY — DO NOT VIOLATE)

The primary user is **elderly, rural, low-literacy, possibly panicking, on a cheap Android phone or a camp kiosk tablet.** Every screen is judged against: *could my grandmother who doesn't read English and has never used an app do this while distressed?*

These are hard rules for the **Pilgrim app** (the officials' dashboard in §11 is a normal data-dense web app and is exempt):

1. **Voice-first, always.** The primary input is a single giant "🎤 बोलिए / Speak" button. The user should never be *required* to type or read to complete the core task. Typing is an optional fallback, never the default path.
2. **The app talks back.** Every screen auto-plays a short spoken instruction (TTS) on load, in the user's chosen language. The user is never expected to read instructions silently. Add a persistent "🔊 सुनिए / Listen again" button on every screen.
3. **One action per screen.** Never present two decisions at once. Linear flow: Language → Speak description → (optional) Photo → Confirm → Result. No menus, no tabs, no nested navigation for the pilgrim.
4. **Minimal text, maximum icon + audio.** Every label is a large icon + one short word, and that word is spoken aloud. Body text ≥ 22px; primary buttons ≥ 28px text. No paragraphs.
5. **Huge touch targets.** Primary buttons fill most of the screen width and are ≥ 80px tall. Generous spacing so a shaky hand can't mis-tap. No small links, no tiny close-buttons.
6. **High contrast, no ambiguity.** Dark text on light background, WCAG AAA contrast. One clear primary action per screen in a single accent color. Disabled/secondary actions are visually obvious.
7. **Impossible to get stuck.** A big "वापस / Back" and "फिर से / Start over" always available. Any error is spoken aloud in plain language with a clear next step ("समझ नहीं आया, फिर से बोलिए" / "Didn't catch that, please speak again"). Never show a stack trace, code, or English error.
8. **Confirm by voice + visual before any submit.** Before sending a report, read the captured details back aloud ("आप ढूंढ रहे हैं: बुज़ुर्ग पुरुष, नीली कुर्ता, तमिल बोलते हैं — सही है?") with a big ✓ Yes / ✗ No.
9. **Instant, obvious feedback on every tap.** Visual press state + a short sound/haptic. When recording: a clear pulsing animation so the user knows it's listening. When processing: a friendly spoken "ढूंढ रहे हैं..." + simple animation, never a blank spinner.
10. **No account, no login, no setup for the pilgrim.** They walk up and use it. Zero friction.
11. **Works on a slow phone and bad network.** Lightweight assets, graceful degradation, never a white screen of death. (See offline mode §13.)
12. **Language picked the easy way.** First screen = large buttons each showing the language **in its own script** (हिन्दी, தமிழ், বাংলা, मराठी, తెలుగు…), and tapping one *speaks the language name aloud* to confirm. Detect probable language from the audio too, but never force the user to read romanized English to choose.

> Implementation note for Claude Code: implement an `useSpeak(text, lang)` hook that wraps the TTS endpoint and is called on every screen mount. Build a reusable `<BigButton icon label labelHindi onPress />` and route **all** pilgrim UI through it so the rules above hold automatically.

---

## 3. Judging Rubric → Build Priorities

Every feature must ladder up to one of these five (from the official slide). Build order is driven by this table.

| Criterion | What it tests | Our decision | Demo proof |
|---|---|---|---|
| **Deployability** — "Could it run at the real Kumbh?" | Runs on infra a govt/NGO actually has | Single Docker image; runs on a cheap VPS **or** an edge box at a camp; no always-on cloud lock-in | "This same container runs on a camp tablet" |
| **Real-world fit** — "Solves a genuine failure" | Attacks a real gap | Reunites a confused elder who **can't state their name**, **across centres**, **across languages** | Demo the exact case loudspeakers can't solve |
| **UX** — "Works for elderly, multilingual users" | Accessibility for the real pilgrim | §2 UX laws: voice-first, app talks back, one action/screen, no install | Speak Hindi → hear Hindi back, never touch a keyboard |
| **System design** — "Handles offline & messy data" | Robustness | Edge mode (local FAISS + sync queue); Claude normalizes vague/misspelled/code-mixed input; top-K confidence, never a brittle hard match | **Pull the network cable mid-demo, matching still works** |
| **Responsible data** — "Privacy by design" | Data ethics | Store embeddings not raw photos where possible; TTL auto-purge after Mela; RBAC on records; **minors never broadcast publicly**; consent at intake; audit log | The minor-match path alerts staff privately, not a public feed |

**Two criteria where we beat a naive photo-matcher and most teams leave points on the table: System design (messy data + offline) and Responsible data (child safety). Invest here.**

---

## 4. Architecture & Stack

**Language: Python.** Single FastAPI monolith. No Go — the ML core (InsightFace, Sarvam SDK, Anthropic SDK, vector ops) is Python-locked, and a two-language split doubles integration risk in a 12-hour build. One artifact ships.

```
                      ┌─────────────────────────────────────────────┐
   Pilgrim (voice)    │                FastAPI backend              │
   ─────────────►  STT │  ┌──────────┐   ┌──────────────────────┐  │
   (Sarvam Saaras)     │  │  Claude  │   │  Matching engine     │  │
                       │  │ extract  │──►│  face + attr + geo   │  │
   Photo  ───────────► │  │ normalize│   │  (InsightFace +      │  │
   (InsightFace embed) │  │ re-rank  │◄──│   pgvector / FAISS)  │  │
                       │  │ announce │   └──────────────────────┘  │
   Audio reply ◄──── TTS│  └──────────┘                            │
   (Sarvam Bulbul)     └────────────────┬────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │   Supabase (Postgres+pgvector) │  ← central
                         │   + local FAISS mirror         │  ← edge/offline
                         └────────────────────────────────┘
        Officials dashboard (React + MapLibre) ◄── reads/writes via API
```

### Component responsibilities
- **Claude (Anthropic SDK)** — the reasoning core. Messy free-text/transcript → structured `Person` profile; cross-language normalization to a canonical English profile for matching; **explainable re-rank** of candidates ("matches on: elderly male, blue kurta, Tamil speaker, near Sangam"); reunification announcement drafting in the target language's native script. Also the MCP orchestration layer if you wire tools.
- **Sarvam (speech only)** — `Saaras` STT (auto-detect Indian language) for intake; `Bulbul v3` TTS for the app's spoken guidance and the reunification announcements. **Nothing else from Sarvam** — translation is done by Claude inside extraction.
- **InsightFace (`buffalo_l`, local on A6000)** — face detection + 512-d embedding. This is the matching primitive; **not Claude's job.** ONNX runtime, GPU.
- **pgvector (Supabase)** — central store of person records + face embeddings; cosine similarity search.
- **FAISS (local)** — edge mirror for offline matching at a camp; syncs to Supabase when online.
- **Frontend** — two surfaces: Pilgrim PWA (kiosk/phone, §10) and Officials dashboard (§11).
- **Docker** — one image, deployable to Fly.io / any VPS / a camp box.

### Key libraries
```
fastapi, uvicorn[standard], pydantic, websockets
anthropic                      # Claude
sarvamai                       # Saaras STT + Bulbul TTS
insightface, onnxruntime-gpu   # face embeddings
faiss-cpu                      # local/offline vector index
supabase, pgvector             # central store
numpy, pillow, python-multipart
```

---

## 5. Repo Structure

```
setu/
├── backend/
│   ├── main.py                 # FastAPI app, route mounting, CORS
│   ├── config.py               # env loading, settings
│   ├── models.py               # Pydantic: Person, MatchResult, Report, etc.
│   ├── db/
│   │   ├── supabase_client.py   # central pgvector store
│   │   ├── faiss_index.py       # local offline index + sync queue
│   │   └── schema.sql           # tables + pgvector setup
│   ├── services/
│   │   ├── speech.py            # Sarvam Saaras (STT) + Bulbul (TTS) wrappers
│   │   ├── claude.py            # extract_profile, normalize, rerank, draft_announcement
│   │   ├── faces.py             # InsightFace embed + similarity
│   │   └── matching.py          # combined scoring engine (§9)
│   ├── routers/
│   │   ├── intake.py           # POST /report/lost, POST /report/found
│   │   ├── match.py            # GET /match/{report_id}, re-rank
│   │   ├── announce.py         # POST /announce (TTS + dashboard event)
│   │   └── ops.py              # officials dashboard data, cases, map
│   └── safety.py               # minor-detection + redaction + audit log
├── frontend/
│   ├── pilgrim/                # PWA kiosk app (§2 UX laws apply)
│   │   ├── screens/            # Language, Speak, Photo, Confirm, Result
│   │   ├── components/BigButton.tsx, SpeakHint.tsx, MicButton.tsx
│   │   └── hooks/useSpeak.ts, useRecorder.ts
│   └── ops/                    # Officials dashboard (React + MapLibre)
├── scripts/
│   └── seed_found_persons.py   # pre-load demo "found" records for the demo
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 6. Data Model

### `Person` (canonical profile — what Claude produces and what we match on)
```python
class Person(BaseModel):
    id: str
    role: Literal["lost", "found"]          # who's being searched for vs logged at a camp
    # structured attributes (Claude extracts; English canonical for matching)
    age_band: Literal["child","teen","adult","elderly","unknown"]
    gender: Literal["male","female","other","unknown"]
    clothing: list[str]                      # ["blue kurta","white dhoti"]
    distinguishing: list[str]                # ["walking stick","scar on left cheek"]
    height_band: Literal["short","medium","tall","unknown"]
    languages_spoken: list[str]              # ["tamil"]
    last_seen_location: str | None           # free text or ghat name
    last_seen_time: str | None
    # raw + provenance
    spoken_language: str                     # detected language of the report
    raw_transcript: str                      # original Saaras transcript (native script)
    native_summary: str                      # short summary in the reporter's language (for readback)
    # media
    face_embedding: list[float] | None       # 512-d InsightFace vector
    photo_ref: str | None                     # storage key (see privacy §12)
    location_hint: str | None                 # Claude vision guess from photo background
    # safety
    is_minor: bool
    contact_phone: str | None
    consent_given: bool
    created_at: datetime
    ttl_expires_at: datetime                  # auto-purge after Mela
```

### Postgres / pgvector (`schema.sql`)
```sql
create extension if not exists vector;
create table persons (
  id uuid primary key default gen_random_uuid(),
  role text not null,
  profile jsonb not null,           -- the structured Person fields
  face_embedding vector(512),
  is_minor boolean default false,
  status text default 'open',       -- open | matched | reunited | expired
  centre_id text,                   -- which camp logged it
  created_at timestamptz default now(),
  ttl_expires_at timestamptz
);
create index on persons using ivfflat (face_embedding vector_cosine_ops);
create table audit_log (
  id uuid primary key default gen_random_uuid(),
  actor text, action text, person_id uuid, meta jsonb, at timestamptz default now()
);
```

---

## 7. Backend API

All endpoints return plain JSON. Errors are user-safe (the pilgrim UI maps them to spoken plain-language messages).

```
POST /report/lost
  multipart: audio (file, optional), photo (file, optional), text (str, optional),
             language_hint (str, optional)
  → { report_id, native_summary, structured: Person, candidates: [MatchResult] }
  Pipeline: audio→Saaras STT → Claude extract+normalize → (photo→InsightFace embed
            + Claude vision location hint) → run matching → return ranked candidates.

POST /report/found
  Same inputs; logs a found person at a centre. role="found".
  Runs reverse matching against open "lost" reports and notifies on hits.

GET  /match/{report_id}
  → { candidates: [MatchResult] }   # re-run / refresh ranking
  MatchResult = { person_id, score, face_score, attr_score, geo_score,
                  explanation, is_minor, centre_id }

POST /announce
  body: { person_id, target_language }
  → { announcement_text, audio_url }
  Claude drafts announcement in native script → Bulbul TTS → returns audio +
  pushes an event to the officials dashboard. BLOCKED for minors (see §12).

POST /speak           # generic TTS for UI guidance
  body: { text, language } → { audio_url }   # Bulbul v3

GET  /ops/cases       # dashboard: all open/matched/reunited cases
GET  /ops/map         # geojson of cases clustered by centre/ghat for MapLibre
POST /ops/confirm     # staff confirm a match → status=reunited + audit
```

---

## 8. Cross-Language Pipeline (Claude does the translation)

Since Sarvam is speech-only, **Claude is the cross-language bridge.** Flow:

1. `Saaras` transcribes the relative's speech **in its native script** (e.g. Tamil text), auto-detecting language.
2. `Claude` receives the native transcript and, in **one call**, does: (a) translate-understand, (b) extract the structured `Person`, (c) emit a `native_summary` back in the reporter's language for the spoken readback, and (d) normalize all attributes into **canonical English** (`clothing: ["blue kurta"]`, `languages_spoken: ["tamil"]`).
3. Matching runs entirely on the canonical English structured fields + face embedding, so a **Tamil report matches a Marathi found-log** automatically.
4. For the announcement, `Claude` writes the text in the **target language's native script** (Devanagari/Tamil/etc.), which is handed straight to `Bulbul` — Bulbul needs native script for correct pronunciation, never romanized.

> Prompt design: give Claude a strict JSON schema for `Person` and instruct "return ONLY JSON, no preamble." Parse defensively, strip code fences. Keep one canonical extraction prompt reused for both lost and found intake.

---

## 9. Matching Engine (`services/matching.py`)

Combine three signals into one score. Never a hard binary match — always return ranked top-K with confidence, because real data is messy.

```python
def score(query: Person, cand: Person) -> MatchResult:
    # 1. Face similarity (cosine of InsightFace embeddings), 0..1
    face = cosine(query.face_embedding, cand.face_embedding) if both_have_faces else None

    # 2. Attribute overlap (structured fields), 0..1
    #    weighted: age_band, gender (high weight); clothing, distinguishing (medium);
    #    height, language (low). Use set overlap + exact matches.
    attr = weighted_attribute_overlap(query, cand)

    # 3. Geographic proximity, 0..1
    #    from last_seen_location / centre / Claude photo location_hint.
    #    same ghat = 1.0, adjacent = 0.6, unknown = neutral 0.5
    geo = geo_proximity(query, cand)

    # Combine. If face available, it dominates; else lean on attributes.
    if face is not None:
        final = 0.6*face + 0.3*attr + 0.1*geo
    else:
        final = 0.7*attr + 0.3*geo

    return MatchResult(score=final, face_score=face, attr_score=attr, geo_score=geo, ...)
```

**Then Claude re-ranks the top ~10** and writes a one-line human explanation per candidate ("Strong match: elderly male, blue kurta, Tamil speaker, last seen near Sangam ghat — same as found person at Centre 7"). The explanation is the differentiator: a camp volunteer confirms in seconds. Return candidates sorted, each with score breakdown + explanation, so the UI can show "क्यों match हुआ" (why it matched).

**Vector search:** central path queries pgvector (`<=>` cosine). Offline path queries the local FAISS index. Same `Person` records, two indices.

---

## 10. Frontend — Pilgrim App (PWA kiosk/phone)

**§2 UX laws are mandatory here.** Five linear screens. Each auto-speaks its instruction on load and has a 🔊 Listen-again button and a big Back button.

**Screen 1 — Language.** Grid of large buttons, each the language in its own script (हिन्दी, தமிழ், বাংলা, मराठी, తెలుగు, ગુજરાતી, ಕನ್ನಡ, മലയാളം…). Tapping speaks the language name aloud and proceeds. Title spoken: "अपनी भाषा चुनिए."

**Screen 2 — Speak.** One huge 🎤 button: "किसे ढूंढ रहे हैं? बोलिए।" (Who are you looking for? Speak.) Press-and-hold or tap-to-toggle recording with a clear pulsing "सुन रहे हैं…" animation. On release → Saaras → Claude. Show the recognized `native_summary` and **read it back aloud**.

**Screen 3 — Photo (optional, skippable).** "अगर फोटो है तो दिखाइए" with a giant camera button and an equally giant "फोटो नहीं है, आगे बढ़िए" (no photo, continue) button. Never block progress on a photo.

**Screen 4 — Confirm.** Read the full captured profile aloud ("आप ढूंढ रहे हैं: बुज़ुर्ग पुरुष, नीली कुर्ता, तमिल बोलते हैं — सही है?"), big ✓ हाँ / ✗ नहीं. ✗ returns to Speak.

**Screen 5 — Result.** Spoken: "हमें ये लोग मिले" (we found these people). Show top candidates as **large cards**: photo (if allowed) + spoken/visual reason + a "📞 इनसे मिलिए / Connect" button that triggers `/announce` (or routes to staff for minors). If no strong match: spoken reassurance + "हमने आपकी जानकारी दर्ज कर ली है, मिलते ही बताएंगे" (we've registered you and will alert you on a match) — never a dead-end "no results."

Tech: React PWA, installable, service worker for offline shell. Audio via `useSpeak`. Recording via MediaRecorder in `useRecorder`. All buttons via `<BigButton>`. Keep bundle small; test on a throttled connection.

---

## 11. Frontend — Officials Dashboard (React + MapLibre)

Normal data-dense web app for camp staff / administration (exempt from §2). Shows the "this is deployable and runs operations" story.

- **Live map** (MapLibre — open-source, no Google key; reads better to a govt judge) of open cases clustered by centre/ghat. Heat shows where separations concentrate.
- **Case queue:** open / matched / reunited, filterable by centre, with the Claude match explanation visible.
- **Match review:** staff sees candidate pairs + score breakdown + explanation, confirms or rejects → `/ops/confirm` → status `reunited`, written to audit log.
- **Minor cases:** flagged, shown only to authorized staff, **never** auto-announced — staff runs the guardian-verification step (§12).
- **Announcement panel:** trigger a reunification announcement (TTS audio) for adult matches; play/preview the Bulbul audio.

---

## 12. Child Safety & Responsible Data (FREE POINTS — DO NOT SKIP)

The government's existing protocol is explicit and we honor it. Bake these in and **narrate them in the demo**:

1. **Minors are never broadcast publicly.** If `is_minor` is true (Claude flags age_band child/teen, or stated age < 18), `/announce` is **blocked** from public TTS. Instead the system creates a **private staff alert** at the nearest centre and opens a **guardian-verification** task. (Mirrors the real rule: don't publicize a child's details until the child is safe; verify the guardian is fit before handover.)
2. **Guardian verification step** for minors/vulnerable: staff confirms the claimant's relationship and fitness before any reunion is marked complete; if doubtful, escalate to police. Represent this as a checklist in the dashboard.
3. **Data minimization.** Prefer storing the **face embedding (a vector), not the raw photo**, for matching. If a photo must be kept, store a reference with restricted access, not in any public response.
4. **TTL auto-purge.** Every record has `ttl_expires_at`; a cleanup job marks/deletes records after the Mela. Personal data is not retained indefinitely.
5. **Consent at intake.** A simple spoken consent ("क्या हम आपकी जानकारी ढूंढने के लिए इस्तेमाल कर सकते हैं?") before storing; `consent_given` recorded.
6. **RBAC + audit log.** Camp staff vs admin roles; every match-confirm, announcement, and record access is written to `audit_log`. (You designed RBAC at JD Jones — speak to this with authority.)
7. **No personal data in URLs/logs.** Never put phone numbers or names in query strings or plaintext logs.

> One-liner for judges: "We keep the government's child-safety protocol intact — a found child is never announced to a public feed; staff are alerted privately and verify the guardian before handover."

---

## 13. Offline / Resilience (System-Design Points)

The "handles offline & messy data" criterion is on the slide — make it visible.

- **Edge mode:** the same container runs at a camp with a **local FAISS index**. Intake + face matching + attribute matching all work with **no internet**. (Claude/Sarvam calls degrade gracefully — see fallback below.)
- **Sync queue:** records created offline are queued and pushed to the central Supabase/pgvector store when connectivity returns; central records sync down. Last-write-wins is fine for the hackathon.
- **Graceful degradation when cloud APIs are unreachable:** if Saaras/Claude are unreachable, fall back to a typed/attribute form + local face-only matching, so the camp is never fully down. Show a small "ऑफलाइन मोड" banner, keep working.
- **Messy-data handling is the Claude superpower:** the system must accept "buzurg aadmi, neeli kurta, Tamil bolte hain," misspelled names, code-mixed Hinglish, blurry photos — and still produce a usable structured profile + ranked candidates. **Demo this with deliberately messy input.**

> **Demo mic-drop:** physically disconnect the network mid-demo and show the camp kiosk still matching against the local index. The slide literally rewards this.

---

## 14. Sarvam + Claude Integration Notes

**Sarvam (speech only):**
- `pip install sarvamai`; key from dashboard.sarvam.ai (₹100 free credits, ample for a demo).
- `Saaras` STT — real-time REST, auto language detect, returns native-script transcript.
- `Bulbul v3` TTS — pass **native-script** text + `target_language_code` + speaker; returns audio. Used for both UI guidance and announcements.
- Free Starter limits (60 req/min STT, 30 req/min for bulbul:v3) are far beyond demo needs.

**Claude (Anthropic API, via the event credits):**
- Set up a Console account at platform.claude.com before the event; load the event API credits there.
- **Gotcha:** if `ANTHROPIC_API_KEY` is set in your shell, Claude Code bills the API account instead of your Max plan. Keep coding on Max (don't set the env var in the Claude Code shell), and use the API key only inside the app (`backend/.env`). Run `claude logout && claude login` with Max creds if needed.
- One reused extraction prompt (strict JSON schema, "return ONLY JSON"); one re-rank prompt; one announcement prompt.

**Face matching (local, no API):** InsightFace `buffalo_l` on the A6000 via onnxruntime-gpu. Embed once at intake, store the 512-d vector.

---

## 15. Build Order (12 hours — strict priority)

Build the **demo-critical path first**. A working thin slice beats a broad half-thing.

**Phase 0 — Setup (30 min).** Repo skeleton, `.env`, Docker stub, Supabase project + `schema.sql`, Sarvam + Anthropic keys verified with one test call each. Seed script ready.

**Phase 1 — Core matching path, no UI (2.5 h).** `POST /report/found` (seed a few via `scripts/seed_found_persons.py`) + `POST /report/lost` → Saaras → Claude extract → InsightFace embed → matching → ranked candidates with explanations. Test entirely via curl/Swagger. **This is the heart — get it working before touching frontend.**

**Phase 2 — Pilgrim PWA happy path (3 h).** Screens 1→5 with `useSpeak` + `useRecorder` + `<BigButton>`. Voice in, audio guidance, photo, confirm-readback, result cards. Apply §2 laws as you build, not after.

**Phase 3 — Officials dashboard (2 h).** MapLibre case map + case queue + match review + confirm. Wire `/ops/*`.

**Phase 4 — The differentiators (1.5 h).** (a) Minor-safety branch (block public announce, private staff alert, verification checklist). (b) Offline mode: local FAISS + the network-cable demo. (c) Announcement TTS for adult matches.

**Phase 5 — Polish + demo rehearsal (1.5 h).** Seed realistic messy demo data, rehearse the §16 script end-to-end, time it, prepare for the network-cut moment, write the 1-line pitch. Deploy the container so there's a live URL.

> If time runs short, cut in this order: dashboard polish → announcement audio → extra languages. **Never cut:** the voice-first pilgrim happy path, the messy-data demo, or the child-safety branch — those are three of the five rubric lines.

---

## 16. Demo Script (rehearse this)

1. **Frame (15s):** "At Kumbh, a lost elder's *name* is shouted over loudspeakers and the family must happen to hear it — across 40 crore people, across languages. We replace that with matching."
2. **Pilgrim flow (60s):** On the kiosk, tap हिन्दी (it speaks the name). Tap 🎤 and say, in Hindi, a messy description of a missing elderly Tamil-speaking man in a blue kurta near Sangam — *don't* state a name. Show the spoken readback. Snap/seed a photo. Confirm. → Top candidate appears with the spoken reason "क्यों match हुआ."
3. **Cross-language point (15s):** "The family spoke Hindi; this person was logged at a camp in Tamil. It still matched — Claude normalized both."
4. **Officials view (20s):** Flip to the dashboard: the case on the map, staff confirms the match → marked reunited, written to the audit log.
5. **Child-safety beat (15s):** Run a *minor* case → show it does **not** broadcast; it privately alerts staff and opens guardian verification. "We honor the government's protocol."
6. **Mic-drop (15s):** Pull the network cable. Kiosk still matches against the local index. "Runs at a camp with no internet."
7. **Close (10s):** "Augments the existing Bhula-Bhatka network, works for the elderly in any language, runs offline, protects children. Deployable at Kumbh 2027."

---

## 17. Setup & Env

`.env.example`:
```
ANTHROPIC_API_KEY=          # app-side only; do NOT export in your Claude Code shell
SARVAM_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
FACE_MODEL=buffalo_l
TTL_DAYS=45
```

Run:
```
docker compose up           # backend + both frontends
python scripts/seed_found_persons.py   # load demo found-persons before demoing
```

---

## 18. Scope Guardrails (what's REAL vs STUBBED)

**Real for the demo:** voice intake (Saaras), Claude extraction + cross-language normalization + explainable re-rank, InsightFace face matching, pgvector + local FAISS, pilgrim PWA happy path, officials dashboard, minor-safety branch, offline matching, announcement TTS.

**Stub / architect-only (show on the diagram, say "deployment path"):** IVR/toll-free (Exotel) and WhatsApp (Meta WABA) intake channels — these are how it reaches a pilgrim with no smartphone in production, but build the **web kiosk** for the demo and present IVR/WhatsApp as the rollout path. Judges reward "here's what's live + here's the path to a toll-free number tomorrow" over a half-broken IVR.

**Definition of done:** the §16 script runs end-to-end without a crash, on the deployed URL, including the messy-input match, the cross-language match, the minor-safety branch, and the offline network-cut moment.
