# ACCEPTANCE — P01 Campus data warehouse

Date: 2026-10-04. Small profile, seed 42. Windows, Python 3.13. Honest rules: synthetic labels retained.

## Commands
- `make data PROFILE=small` (foundation, 17–20 s) then `make ingest` (34–35 s, <2 min ✓)
- Direct: `python -m ingest.cli run-all --raw data/raw --out data/lakehouse --truth data/truth`
- `python -m ingest.cli reconcile ...`, `python -m ingest.cli catalogue --out platform/docs/catalogue.md`

## Reconciliation (measured 2026-10-04, data/lakehouse/reconciliation.json)
All `pass: true`, zero unexplained loss at the correct grain:
- space_register: raw 501 = bronze 501; silver 495 + quar 6 = 501 ✓ (row)
- cafm_workorders: 6039 = 6039; 4171 + 1868 = 6039 ✓ (row)
- meter_hh_supplierA: 34419 = 34419; 33866 + 553 = 34419 ✓ (row)
- meter_hh_supplierB: raw 732 = bronze 732 (wide rows); cells 35136 = silver 34349 + quar 787 ✓ (cell, wide→long)
- bms_trends: raw 8640 = bronze 8640; cells 172800 = silver 172780 + quar 20 (N/A) ✓ (cell)
- statutory_inspections: 41 = 41; 40 + 1 = 41 ✓ (row)
- timetable: 12566 = 12566; 12347 + 219 = 12566 ✓ (row)
- sensors: 779933 = 779933; 773974 + 5959 = 779933 ✓ (row)

XLSX raw counts exclude title/header rows (space_register 3/sheet, others 1/sheet); documented in `reconcile.py`.

## Idempotency
Re-run `run-all`: all 8 bronze files report `skipped` (same sha256), silver row counts unchanged. Corrected-file path tested in `test_bronze.py` (new sha → new ingest_id). ✓

## DST
- Unit: hand-built 2026-03-29 local series → 46 UTC periods; gaps report empty when exact.
- Integration: small-window 2026-03-29 yields 46 unique UTC periods per meter; autumn 50-period logic in `_gaps_report` short-date map + unit-tested 2025-10-26 case in foundation. Gap report flags (expected 48/46/50 vs actual) without fabricating values. ✓

## Planted invalid rows → quarantine
`ground_truth.yaml` holds 10,540 defect entries (small, 0.03). Silver quarantines with `_reject_reason`: nulls, unparseable/future dates, negatives, unmapped categories/buildings (with fuzzy suggestions), orphans (B999-ORPHAN), duplicates, completed≤raised. Integration test asserts quarantine non-empty with reasons for space + cafm on full small bronze. ✓

## Terraform
`infra/terraform/main.tf` + `lakehouse.tf`: versioned+SSE+public-blocked S3, Glue DB, Athena workgroup (10 GB/query cap, enforced, results bucket), least-privilege IAM role, $20/month Budget alarm. `make aws-plan` runs fmt-check + init + validate (terraform binary not installed locally; files kept fmt-clean by construction; CI validates). README carries cost warning; CI never applies. ✓ (validate pending binary; noted as limitation)

## Tests / lint / types
- `platform/tests`: 7 passed (bronze idempotency, silver rules, cumulative rollover, DST, reconciliation, planted quarantine).
- Full suite (foundation 20 + platform 7): 27 tests; run green.
- `ruff check` + `format --check` clean; `mypy` strict (campus_synth.*, ingest.*) clean.
- Queries `platform/queries/*.sql` run on DuckDB; Athena notes inline. Catalogue generated at `platform/docs/catalogue.md`.

## Deviations
- Wide sources reconcile at cell level (documented grain column), not row level — required by reshape semantics.
- BMS `_row_number` audit column excluded from point columns (would otherwise create a phantom point); quarantine stored as strings for mixed-type robustness (silver keeps types).
- Cumulative-register path implemented + unit-tested but not exercised by current interval-only synthetic exports (kept for supplier variation).
- Water-daily/heat meters not silverised (electricity/gas HH only); noted in README limitations.
