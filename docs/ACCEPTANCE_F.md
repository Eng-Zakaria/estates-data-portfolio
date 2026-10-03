# ACCEPTANCE — Foundation `campus_synth` (spec `00-foundation-campus-synth.md`)

Date: 2026-10-03. Profile `small`, seed 42 unless stated. Machine: Windows, Python 3.13, pandas 2.3, pyarrow 21.

## CLI

- `campus-synth generate --profile small|default --seed 42 --out data/raw [--defects 0..1] [--format …]` ✓
- `campus-synth truth --out data/raw/ground_truth.yaml` ✓ (planted-only re-emit; `generate` writes planted+defect log)
- `campus-synth snapshots --weeks 12 --out data/raw_snapshots` ✓ (defect 0.12→0.01, manifest per week)

## Profiles & performance

- `small`: 8 buildings, 3 months (2026-01-01→2026-03-31), 500 spaces. `generate_all` 7.9 s; full `generate`+exports 17–20 s. **<30 s ✓**
- `default`: 40 buildings, 24 months, 3,000 spaces / 12,000 assets / 60,000 WOs / 130 meters (code paths identical; full run not in CI for time/size; estimate <5 min, <1.5 GB from small scaling: truth 3.8 MB → ~150 MB, raw ~7 MB → ~300 MB).
- Seeded RNG only (`make_rng`); determinism test hashes (small, seed 42, first 16 hex):
  buildings 8 `100e341bda341389`, spaces 500 `463b60454d5d7e7a`, assets 1496 `7beb616ea4fa07a6`, meters 16 `3536950bd1f4b7af`, work_orders 6000 `e5821b0485bf701b`. Same seed → same; seed 43 differs. **Byte-identical (truth parquet) ✓**

## Entities & IDs

`B001…`, `S-B001-L02-014`, `A-B001-000123`, `M-B001-E01`, `SN-…`, fake 22-char IFC GUIDs for ~60% spaces/assets. All 17 truth tables present in `data/truth/*.parquet` (buildings, floors, departments, spaces, assets, work_orders, inspection_types, inspections, meters, meter_readings_hh, weather, academic_calendar, timetable_events, sensors, sensor_readings, cost_pools, activity_splits). ✓

Realism: electricity base+occupancy/day/noise by use (labs high, libraries long hours, residences evening peak); gas base+HDD; UTC store with local-time exports; WO age/condition rates + lognormal costs; timetable 09–18 teaching weeks with mismatches + ~15% effective no-shows via small groups; CO₂ first-order (EWMA) to occupancy. ✓

## Messy exports (all 7 + ground truth)

- `space_register_YYYYMMDD.xlsx` (sheets/campus, merged titles, names-not-IDs, `Teaching/teaching/TEACH/Teachig` variants, `12.3 m2/sqm`, blank row) ✓
- `cafm_workorders_YYYYMMDD.csv` (renamed headers, 3 date formats, `Complete/COMP/Closed`, `£1,234.56`, duplicates, completed=raised) ✓
- `meter_hh_supplierA_YYYYMMDD.csv` long + local `dd/mm/yyyy HH:MM` + gaps; `meter_hh_supplierB_YYYYMMDD.csv` wide 48 cols/day ✓
- `bms_trends_YYYYMMDD.csv` wide 1 col/point, ISO+offset, `N/A`, units in header ✓
- `statutory_inspections_YYYYMMDD.xlsx` free-text + Excel serials ✓
- `timetable_YYYYMMDD.csv` (`09:00-11:00`, `1-10,12`) ✓
- `sensors_YYYYMMDD.parquet` + drift/stuck/dropout ✓
- `ground_truth.yaml` planted + 10,540 defect log entries (small, defects 0.03) ✓

## Defects (`--defects` default 0.03)

`inject_defects(df, spec)` implements duplicate/null/out-of-range/orphan/misspelt/future (+ gaps/rollover/DST/unit-mixup/stale represented in export-specific code and logged). Counts == logs (test). ✓

## Planted findings (`ground_truth.yaml`)

Small `applies=True` verified in `test_planted.py`: B007 overnight 0.45–0.75 of p99 (spec 0.60); B003 dense booking + mean occ <0.35; D-ENG ≥1.3× median (spec ~1.4×); legionella ≥3 overdue + ≥2 failed remedial >90 d; B005 worst-room CO₂ (conservative >5% over 1500 in test; full occupied-time ≥20% in evidence query); SN-0042 drift (late mean > early mean); IFC 12 area-diff + 5 missing. Default-only (B012 ≥8 reactive, B019 summer >1.5× June, M-B015 5-day flatline, PPM 2025-Q4 drop) verified by targeted fast generation. ✓

## Tests

`pytest`: **20 passed**. Coverage **96% total** (generator 98, defects 100, exports 97, schemas 100, cli 91). Schema (Pydantic) all tables + negative; integrity zero orphans + NIA ≤ GIA; DST spring 46 / autumn 50 + small-window 2026-03-29 46; determinism hashes. `ruff check` + `format --check` clean; `mypy` strict clean. ✓

## Docs

`docs/DATA_MODEL.md` (Mermaid ER + export map) ✓. Package README: why-synthetic + full planted list ✓. Root `DATA.md` (no external; placeholders for later) ✓. `docs/OPEN_QUESTIONS.md` (DESNZ/Uniclass/COBie/ISO19650/HESA/BDG2/CO₂ guides) ✓.

## Deviations from spec

- Python 3.11+ (dev 3.13) vs spec 3.12; compatible syntax, CI matrix 3.11/3.12. No ADR needed (compatible range).
- `truth` command emits planted-only; `generate` writes planted+defects (avoids clobber; Makefile `data` runs `generate` only).
- `uniclass_code_true` is `DEV_PLACEHOLDER_*` (hard rule: never invent codes; P13 fetches NBS).
- `uv.lock` not committed (network-gated); dependencies pinned in `pyproject.toml`, lock to be generated in CI/networked env.
