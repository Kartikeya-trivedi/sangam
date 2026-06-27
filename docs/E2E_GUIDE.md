# SETU — End-to-End Run & Test Guide

How to bring SETU up with **real Sarvam + Anthropic keys** and run a full voice user-test.

> Status note: `backend/services/speech.py` (Sarvam STT/TTS) is being wired. The correct SDK
> calls are in [§5](#5-sarvam--anthropic-wiring-reference) so the voice path works once it lands.
> Everything else (Claude extract, matching, dedup, UI) already runs.

---

## 1. Prerequisites
- **uv** (Python) — https://docs.astral.sh/uv/ · **Node 20+** · (optional) **Docker**
- **Sarvam key** — dashboard.sarvam.ai (₹100 free credits; free tier 60 STT/min, 30 TTS/min)
- **Anthropic key** — platform.claude.com (load the event API credits)

## 2. Keys & env
Create `backend/.env` (copy from `.env.example`):
```
ANTHROPIC_API_KEY=sk-ant-...
SARVAM_API_KEY=sk_...
ANTHROPIC_MODEL=claude-haiku-4-5      # cheap+fast for extraction; opus for the final demo
# SUPABASE_URL / SUPABASE_KEY optional — without them it runs on the local FAISS store
OFFLINE_MODE=false
```
> ⚠️ **Do NOT `export ANTHROPIC_API_KEY` in your shell** — it must live only in `backend/.env`,
> or Claude Code bills the API account instead of your Max plan.

## 3. Run the backend
```bash
cd backend
uv sync                 # add --extra faces on a GPU box for InsightFace
uv run uvicorn main:app --reload --port 8000
```
Open **http://localhost:8000/docs** (Swagger) — this is the easiest way to test every endpoint.

## 4. Verify the keys BEFORE the UI test
Use Swagger (or curl). Confirm each integration in isolation:

1. `GET /health` → `{"anthropic": true, "sarvam": true, ...}` (keys detected).
2. `POST /speak` `{"text":"नमस्ते, परीक्षण","language":"hi-IN"}` → returns audio (Bulbul reachable).
3. `POST /report/lost` with **text** (no audio): `text = "buzurg aadmi, neeli kurta, Tamil bolte hain"` →
   returns a structured `Person` + `native_summary` (Claude extraction works).
4. Seed found-people so matches appear, then re-run step 3 and check `candidates[]`:
   ```bash
   uv run python ../scripts/load_dataset.py --limit 300       # real dataset, as "found"
   # or the small curated set:
   uv run python ../scripts/seed_found_persons.py
   ```
5. `POST /announce` `{person_id, target_language}` → announcement text (+ audio for adults;
   **blocked** for minors — that's the child-safety path, expected).

If 1–5 pass, the pipeline is healthy.

## 5. Sarvam + Anthropic wiring reference
For whoever implements `speech.py` — exact current SDK (verified against Sarvam docs):
```python
from sarvamai import SarvamAI
client = SarvamAI(api_subscription_key=settings.sarvam_api_key)

# STT — native-script transcript + auto language detect.
# Use SAARIKA (transcription). 'saaras' is the *translate* model; we don't want that because
# Claude does the translation (spec §8). language_code="unknown" => auto-detect.
r = client.speech_to_text.transcribe(file=open("clip.wav","rb"),
                                     model="saarika:v2.5", language_code="unknown")
text, lang = r.transcript, r.language_code        # lang e.g. "hi-IN"

# TTS — text MUST be native script (never romanized). Returns base64 wav in .audios[0].
import base64
resp = client.text_to_speech.convert(text=native_script_text,
                                     target_language_code="hi-IN",
                                     model="bulbul:v3", speaker="anushka")
audio_bytes = base64.b64decode(resp.audios[0])
```
Anthropic extraction is already wired (`services/claude.py`); just set the key. For cost, use
`claude-haiku-4-5` for extraction/rerank, `claude-opus-4-8` for the live demo.

## 6. Run the frontends
```bash
cd frontend/pilgrim && npm install && npm run dev   # http://localhost:5173
cd frontend/ops     && npm install && npm run dev   # http://localhost:5174
```
`VITE_API_BASE` defaults to `http://localhost:8000`.

## 7. The e2e user test (pilgrim)
1. Open the pilgrim app → tap **हिन्दी** (it speaks the name back).
2. Tap 🎤 and say, in Hindi, a *messy* description of an elderly Tamil-speaking man in a blue
   kurta near a ghat — **do not state a name**.
3. Confirm screen reads the captured summary **back aloud** → tap ✓ हाँ.
4. Result screen shows ranked candidates with a spoken "क्यों match हुआ" reason.
5. Tap 📞 **Connect** on an adult match → announcement is generated/played.
6. **Cross-language proof:** the family spoke Hindi; the matched person was seeded in another
   language — it still matched (Claude normalized both).

**Offline test (system-design proof):** stop the network / set `OFFLINE_MODE=true` and restart —
the app still matches against the local FAISS store; STT/Claude degrade to the typed path + browser TTS.

**Child-safety test:** report/find a child case → `/announce` is **blocked**, a private staff
alert is created (visible on the ops dashboard), never a public announcement.

## 8. Troubleshooting
| Symptom | Fix |
|---|---|
| Mic does nothing on phone / LAN IP | `getUserMedia` needs a **secure context** — use `localhost`, or HTTPS (tunnel via `cloudflared`/`ngrok`, or `vite --https`). |
| `/health` shows `sarvam:false`/`anthropic:false` | Key missing/typo in `backend/.env`; restart uvicorn (env is read at startup). |
| STT returns empty / wrong model error | Use `saarika:v2.5` (not deprecated v1/v2); `language_code="unknown"` for auto-detect. |
| TTS garbled pronunciation | Pass **native-script** text to Bulbul, never romanized; ensure `target_language_code` matches. |
| CORS error in browser | Backend allows `*` already; confirm `VITE_API_BASE` points at the right host:port. |
| Claude bills the wrong account | `ANTHROPIC_API_KEY` is set in your shell — unset it; keep it only in `backend/.env`. |
| 429 from Sarvam | Free tier is 60 STT/min, 30 TTS/min — cache fixed UI prompts (see [INFRA.md](INFRA.md)). |
