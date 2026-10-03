# PLAN: Foundation `campus_synth`

## Goal
Implement shared synthetic campus generator per `docs/specs/00-foundation-campus-synth.md`. No other project.

## Tasks
1. [x] Scaffold repo layout (AGENTS.md, docs/specs, packages/campus_synth, data/, docs/)
2. [ ] Implement `packages/campus_synth`:
   - `config.py` – profiles small/default, Pydantic
   - `utils.py` – seeded RNG, IFC GUID, time helpers (UTC store, Europe/London export), DST helpers
   - `generator.py` – truth tables (buildings→activity_splits), realistic profiles, planted findings
   - `exports.py` – 7 messy source-system exports
   - `defects.py` – `inject_defects` + catalogue
   - `ground_truth.py` – planted findings registry + defect log → `ground_truth.yaml`
   - `schemas.py` – Pydantic v2 validators per truth table
   - `cli.py` – `generate`, `truth`, `snapshots` (Typer)
3. [ ] Tests: determinism, schema, integrity, defects, DST, planted
4. [ ] Docs: `docs/DATA_MODEL.md` (Mermaid ER + export map), package README (why synthetic + findings), root `README/DATA/STATUS/OPEN_QUESTIONS`
5. [ ] Makefile + pyproject + CI minimal (lint/type/test/dbt-stub) + `make ci` green
6. [ ] Acceptance evidence: run small profile, capture timings, row counts, hashes

## Risks & mitigations
- **Parquet/xlsx determinism**: sort rows, fixed timestamps, `float_format` stable; hash test covers truth parquet only (xlsx has OOXML timestamps) — document.
- **Performance default (4.5M HH rows)**: vectorised numpy/pandas, no per-row loops for readings; chunk by meter.
- **DST correctness**: use `zoneinfo Europe/London`, generate UTC then convert; test 2025-03-30 (46) and 2025-10-26 (50).
- **Referential integrity vs defects**: truth tables always clean; defects only in `data/raw` exports. Integrity tests run on truth.
- **Planted findings fragility**: implement as deterministic overrides after random generation (fixed IDs/dates), verified by tests with tolerances.
- **Python 3.13 vs spec 3.12**: dev machine has 3.13; code targets 3.11+ compatible, CI matrix 3.11/3.12/3.13. No 3.12-only syntax.

## Open questions (non-blocking, recorded in OPEN_QUESTIONS.md)
- DESNZ factors, Uniclass, COBie, ISO19650, HESA specs needed later — not for foundation.
- `uv.lock` generation requires network; if offline, pin in pyproject and generate lock in CI.
- Default-profile full sensor 1.3M rows + HH 4.5M rows size estimate ~600MB parquet — under 1.5GB, verified on run.

## Assumptions
- End date fixed `2026-03-31` for reproducibility (configurable via `--end-date`).
- Small: 8 bldgs, 3 months (2026-01-01→2026-03-31), ~500 spaces, ~26 meters, 30 sensor rooms.
- Default: 40 bldgs, 24 months (2024-04-01→2026-03-31), ~3000 spaces, ~12000 assets, ~60k WOs, ~130 meters, 150 sensor rooms × last 3 months.
- All synthetic; building names anonymised "Building A…" + "Science Block N".
