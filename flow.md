# SETU — System & Data Flow

How a report moves through SETU, end to end. Pairs with [SETU_BUILD_SPEC.md](SETU_BUILD_SPEC.md)
(the *what*), [DATA.md](DATA.md) (the datasets), and [ROLES.md](ROLES.md) (who builds what).
Diagrams are Mermaid and render on GitHub.

## 1. System context

```mermaid
flowchart LR
  P["Pilgrim / family<br/>voice, any language"] --> PA["Pilgrim PWA<br/>Capacitor → Android"]
  V["Camp volunteer"] --> OPS["Ops Dashboard<br/>MapLibre"]
  PA -->|"HTTPS JSON / multipart"| API["FastAPI backend"]
  OPS -->|"HTTPS JSON"| API
  API --> CL["Claude<br/>extract · normalize · rerank · announce"]
  API --> SV["Sarvam<br/>Saaras STT · Bulbul TTS"]
  API --> IF["InsightFace<br/>512-d face embedding"]
  API --> MX["Matching engine<br/>face + attr + geo + dedup"]
  API --> DB[("Supabase<br/>Postgres + pgvector")]
  API --> FA[("Local FAISS<br/>edge / offline")]
  API --> GEO["Geo / hotspots<br/>data/*.csv + *.kml"]
```

## 2. Report a lost person — the core pilgrim flow

```mermaid
sequenceDiagram
  actor F as Family
  participant UI as Pilgrim PWA
  participant API as FastAPI
  participant STT as Sarvam Saaras
  participant CL as Claude
  participant IF as InsightFace
  participant MX as Matching
  F->>UI: pick language, tap mic, describe person (+ optional photo)
  UI->>API: POST /report/lost (audio, photo, language_hint)
  API->>STT: transcribe(audio) - native-script text
  API->>CL: extract_profile - canonical EN Person + native_summary
  opt photo present
    API->>IF: embed(photo) - 512-d vector
  end
  API->>MX: rank_candidates - top-K (face + attr + geo)
  API->>CL: rerank - ordered + "why it matched"
  API-->>UI: report_id, native_summary, candidates[]
  UI-->>F: speak summary to confirm, then show result cards
```

Cross-language is automatic: the family may speak Hindi while the found-person was logged in
Tamil — Claude normalizes both to canonical English fields, so matching just works.

## 3. Report a found person + cross-center dedup — the dataset's hero problem

```mermaid
flowchart TD
  A["Volunteer logs FOUND person at Center X"] --> B["POST /report/found"]
  B --> C["Claude extract → Person (centre_id = X)"]
  C --> D["Persist: FAISS local + Supabase"]
  D --> E["Reverse-match vs open LOST across ALL centers"]
  E --> Fq{"High-score twin<br/>at another center?"}
  Fq -- yes --> G["Surface to staff + link as same person"]
  Fq -- no --> H["Keep open; alert on future match"]
  G --> I{"is_minor?"}
  I -- yes --> J["Private staff alert + guardian verification"]
  I -- no --> K["Adult: announcement allowed"]
```

This closes the real gap: a person logged at Center A is matched against a family searching at
Center B. Measure it with `is_duplicate_report` (see §7).

## 4. Matching engine (`services/matching.py`)

```mermaid
flowchart LR
  Q["Query Person"] --> Fc["face cosine<br/>InsightFace 512-d"]
  Q --> At["attribute overlap<br/>age · gender · clothing · lang · name"]
  Q --> Ge["geo proximity<br/>last_seen → lat/lng, risk-weighted"]
  Fc --> S{"photo on both sides?"}
  S -- yes --> W1["0.6·face + 0.3·attr + 0.1·geo"]
  S -- no --> W2["0.7·attr + 0.3·geo"]
  W1 --> R["top-K ranked"]
  W2 --> R
  R --> CL["Claude rerank + one-line explanation"]
```

Never a hard binary match — always ranked top-K with a confidence breakdown + a human
explanation a volunteer can confirm in seconds.

## 5. Announcement + child safety (§12)

```mermaid
flowchart TD
  A["POST /announce (person_id)"] --> B{"is_minor?"}
  B -- yes --> C["BLOCK public TTS"] --> D["Private staff alert<br/>+ guardian verification"]
  B -- no --> E["Claude drafts native-script text"] --> Tx["Bulbul TTS"] --> G["Audio + dashboard event"]
```

## 6. Offline / edge resilience (§13)

```mermaid
flowchart LR
  subgraph CAMP["Camp box — no internet"]
    UIo["Pilgrim PWA shell"] --> APIo["FastAPI"]
    APIo --> FAo[("Local FAISS")]
    APIo -. degraded .-> FB["typed form + face-only match<br/>browser TTS"]
  end
  FAo -->|"sync queue when online"| DBc[("Supabase pgvector")]
  DBc -->|"pull updates"| FAo
```

If Saaras/Claude are unreachable: fall back to the typed/attribute path + local match, show a small
"ऑफलाइन मोड" banner, keep working. Records queue and sync (last-write-wins) on reconnect.

## 7. Data & geo pipeline

```mermaid
flowchart LR
  CSV["Synthetic_Missing_Persons_2500.csv"] -->|"load_dataset.py"| REG[("Registry: Person records")]
  REG --> MX["Matching / dedup"]
  GT["is_duplicate_report<br/>(ground truth)"] -->|"eval_dedup.py"| MET["precision / recall / F1"]
  K1["Chokepoints_Parking.kml<br/>risk-weighted"] --> HOT["Hotspot heat<br/>+ help-desk placement"]
  K2["CCTV_Zones_Cameras.kml<br/>zones + cameras"] --> COV["Coverage + point-in-zone"]
  POL["Police_Stations.kml"] --> RTE["Nearest help point"]
  LOC["last_seen_location"] --> GP["geo_proximity"]
```

## 8. Ops dashboard flow

```mermaid
flowchart LR
  L["GET /ops/cases"] --> Q["Case queue<br/>open / matched / reunited"]
  M2["GET /ops/map"] --> MAP["Map: case clusters<br/>+ risk hotspots"]
  Q --> RV["Staff reviews candidate pair<br/>+ score + explanation"]
  RV --> CF["POST /ops/confirm"]
  CF --> STt["status = reunited + audit_log"]
```
