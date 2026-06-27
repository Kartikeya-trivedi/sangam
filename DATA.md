# SETU — Dataset Guide (Claude Impact Lab, Mumbai 2026)

Source: [SumeetGDoshi/claude-impact-labs-data](https://github.com/SumeetGDoshi/claude-impact-labs-data/tree/main/claude-impact-lab-mumbai-2026/data)
→ downloaded to `setu/data/`. All missing-person records are **synthetic** (no real PII).

Venue is **Nashik–Trimbakeshwar Simhastha** (≈ 19.98–20.02 N, 73.71–73.83 E) — note the scaffold's
demo coordinates were Prayagraj/Sangam and must be switched to Nashik (see "Next steps").

## Inventory

| File | Rows | Key fields | Geo? |
|---|---|---|---|
| `Synthetic_Missing_Persons_2500.csv` | 2,500 | case_id, reported_at, name, gender, age_band, state/district, language, last_seen_location, reporting_center, mobile, physical_description, status, resolution_hours, **is_duplicate_report**, remarks | place names |
| `CCTV_Locations.csv` | 1,280 | camera_id (`Z{zone}-C{n}`), lon, lat | points |
| `Zone_Boundaries.csv` | 32 | zone_name, centroid_lat/lng, boundary point count (no polygon) | centroids |
| `Police_Stations.csv` | 14 | station_name, lon, lat | points |
| `Chokepoints_Parking.csv` | 85 | location_name, category, lon, lat | points |

## Ground-truth stats (computed)

- **10 reporting centers** → the cross-center search gap is real and measurable.
- **202 duplicate-flagged records (8.1%)** → built-in ground truth for the dedup matcher.
- Incomplete data: **14.8% no name, 19.7% no mobile, 105 blank descriptions**.
- `physical_description` is **noisy** (often describes a different person / generic) → Claude normalization is essential.
- **20 distinct `last_seen_location`** values (named landmarks) — small enough to geocode to coordinates.
- Age skew confirmed: **61–70 largest (697)**, 71–80 (532); **288 minors** (0–12: 201, 13–17: 87) → child-safety branch has real volume.
- Status: 2,150 reunited · 210 pending · 73 hospital · 67 unresolved.
- 13+ languages, no dominant one (Hindi 271 top) → cross-language matching matters.
- Reported 2027-07-01 → 2027-08-14 (~6 weeks) → time-series for snan-day spikes.

## ⚠️ There are no photos/faces in any file

The provided data exercises **text + attribute + geo + cross-center dedup**, *not* face matching.
InsightFace stays a **live-intake** capability (when a family uploads a photo at the kiosk), but the
hero feature for THIS dataset is **cross-center duplicate detection** — and `is_duplicate_report`
lets us report a real precision/recall number. That is a direct hit on *System design* + *Real-world fit*.

## Dataset → SETU component mapping

| Dataset | Powers | Code |
|---|---|---|
| Missing_Persons | Seed the unified registry at scale; cross-center dedup; messy-text normalization; minor volume | `scripts/load_dataset.py` (new), `services/matching.py`, `services/claude.py`, `safety.py` |
| Missing_Persons `is_duplicate_report` | Offline evaluation harness: precision/recall/F1 of the matcher | `scripts/eval_dedup.py` (new) |
| `last_seen_location` → geo | Real distance for `geo_proximity` instead of token overlap | location→coord lookup |
| CCTV_Locations | "Is this spot camera-covered?" coverage layer on the ops map | `routers/ops.py`, ops MapView |
| Zone_Boundaries | Cluster cases by zone centroid on the map | ops MapView |
| Police_Stations | Route a found person/family to nearest help point; response coverage | new `/ops/nearest` |
| Chokepoints_Parking | **Hotspot prediction** — where separations cluster; where to place help desks | ops heat layer / analytics |

## Next steps (recommended order)

1. `scripts/load_dataset.py` — ingest the 2,500 records into the registry (replaces the toy seed). Maps cleanly to `Person` (centre_id ← reporting_center; is_minor ← age_band 0-12/13-17; no face_embedding).
2. `scripts/eval_dedup.py` — run the matcher over the set, compare against `is_duplicate_report`, print precision/recall. **The killer demo metric.**
3. Switch geography to Nashik: real coords for centers + a `last_seen_location → lat/lng` table; feed `geo_proximity`.
4. Ops map: load CCTV / zones / police / chokepoints layers; hotspot heat from chokepoints + case density.
