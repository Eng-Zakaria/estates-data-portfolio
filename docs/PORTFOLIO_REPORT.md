# Estates Data Portfolio — Build Report for Showcase (2026-10-05)

> For the portfolio session: copy sections below into GitHub README / MkDocs / slides.
> All data synthetic unless stated. Sources in `DATA.md`. No real buildings, performance, or compliance implied.

## Snapshot

| ID | Project | Status | Evidence |
|---|---|---|---|
| F | Foundation `campus_synth` | ✅ done 2026-10-03 | 20 tests, 96% cov, small generate 17–20s; `docs/ACCEPTANCE_F.md` |
| P01 | Campus data warehouse (lakehouse) | ✅ done 2026-10-04 | 7 platform tests, ingest 34–35s, 8/8 sources reconciled zero unexplained loss; `docs/ACCEPTANCE_P01.md` |
| P04 | dbt project (gold marts) | ✅ done 2026-10-05 | `dbt build` PASS=196 WARN=0 ERROR=0, 147 data tests + 2 unit, 41/41 models tested, 292/292 cols documented, 21 contracts; `docs/ACCEPTANCE_P04.md` |
| P05 | CI/CD for data | ✅ done 2026-10-05 | 6 workflows + reusable, pre-commit, gates verified locally (ruff+mypy clean, pytest 27 pass, dbt 196 pass, sqlfluff+mkdocs+compose clean); `docs/ACCEPTANCE_P05.md` |
| P06 | Space utilisation | ✅ done 2026-10-05 | freq×occ on gold + observed occupancy, 7 calc tests, 5 validation SQL, full Power BI handoff; `projects/p06-space-utilisation/README.md` |
| P08 | Net zero & carbon | ✅ done 2026-10-05 | scopes/intensity/pathway/baseload, 7 calc tests, 4 validation SQL, full Power BI handoff; `projects/p08-net-zero-carbon/README.md` |
| P02 | Orchestrated ETL (Airflow) | 🔨 in-progress on `p02-orchestration` (3 commits, 964 lines, 15 files) | 7 DAGs + pure task logic + contract tests; not merged |
| P03 | Data quality framework | 🔨 in-progress on `master` (4 commits) | 133 YAML checks across 10 datasets, GX 1.23.2 verified, recall/scoring/alerts/runner+CLI; STATUS still ☐, no acceptance yet |
| P07, P09–P20 | — | ☐ not started | Specs in `docs/specs/` |

Branch note (2026-10-05 18:32–18:45): `master` at `b0f7796` (P03), `p02-orchestration` at `4be7fae` (+3 P02 commits). `rogue/drafts-2026-10-05` stale at `137549e`. `stash@{0}` holds rescued P04 work (already re-committed as `2177f2b` — verify before dropping).

---

## F — Foundation generator (`packages/campus_synth/`)

**Problem:** need a shareable, reproducible campus dataset that looks like real estates exports (messy) but has known ground truth.

**Built:**
- 17 truth tables (buildings, floors, departments, spaces, assets, work_orders, inspection_types, inspections, meters, meter_readings_hh, weather, academic_calendar, timetable_events, sensors, sensor_readings, cost_pools, activity_splits) with IDs `B001…`, `S-B001-L02-014`, `A-B001-000123`, `M-B001-E01`, `SN-…`, 22-char IFC GUIDs for ~60% rows.
- 7 messy exports + `ground_truth.yaml`: `space_register.xlsx` (merged titles, `Teaching/teaching/TEACH/Teachig`, `12.3 m2/sqm`, blank row), `cafm_workorders.csv` (3 date formats, `Complete/COMP/Closed`, `£1,234.56`, duplicates), `meter_hh_supplierA.csv` long + `supplierB.csv` wide 48 cols/day, `bms_trends.csv` wide + `N/A`, `statutory_inspections.xlsx` free-text + Excel serials, `timetable.csv` (`09:00-11:00`, `1-10,12`), `sensors.parquet` drift/stuck/dropout.
- `inject_defects` + catalogue, planted findings registry, Pydantic validators, Typer CLI (`generate`, `truth`, `snapshots`), 12-week snapshots with defect 0.12→0.01.
- Realism: electricity base+occupancy/day/noise by use, gas base+HDD, UTC store / Europe/London export, DST 2025-03-30 (46) / 2025-10-26 (50), WO age/condition + lognormal costs, timetable mismatches + ~15% no-shows, CO₂ EWMA.

**Measured:** small (8 bldgs, 3 months, 500 spaces): `generate_all` 7.9s, full +exports 17–20s (<30s ✓). Determinism hashes (seed 42): buildings `100e341b`, spaces `463b6045`, assets `7beb616e`, meters `3536950b`, WOs `e5821b04`; seed 43 differs. Default estimate <5min, <1.5GB. Tests 20 passed, cov 96% (generator 98, defects 100, exports 97, schemas 100, cli 91). ruff+mypy strict clean.

**Show it:** `docs/DATA_MODEL.md` Mermaid ER, package README planted list, `make data PROFILE=small`.

## P01 — Lakehouse (`platform/src/ingest/`, `infra/terraform/`)

**Problem:** land messy exports without loss, clean to queryable silver, prove every row accounted for.

**Built:** bronze (sha256 idempotent, `skipped` on re-run, corrected-file new `ingest_id`) → silver (typed, `_reject_reason` quarantine, fuzzy suggestions, orphans `B999-ORPHAN`) → `reconcile` (row-level except wide sources at cell-level) → `catalogue.md`. DST gap report (48/46/50) without fabrication. Cumulative-register path (unit-tested, interval-only synthetic). Terraform: versioned+SSE S3, Glue DB, Athena workgroup 10GB cap, least-privilege IAM, $20 Budget alarm.

**Measured (small seed 42, `reconciliation.json`):** all `pass:true`:
space 501=501 (495+6), cafm 6039=6039 (4171+1868), meterA 34419 (33866+553), meterB cells 35136=34349+787, BMS cells 172800=172780+20, inspections 41 (40+1), timetable 12566 (12347+219), sensors 779933 (773974+5959). `make ingest` 34–35s. Tests 7 passed. Known gap: `dates.py` missing TZ-aware ISO candidate → ~30% legit CAFM in quarantine (`docs/OPEN_QUESTIONS.md` §11) — tracked by P03, fix scheduled.

**Show it:** `platform/README.md` diagram, `platform/docs/catalogue.md`, `platform/queries/*.sql`.

## P04 — dbt (`platform/dbt/`)

**Problem:** turn silver into governed gold marts P06–P10 can trust.

**Built:** 4 seeds, 2 snapshots (`snap_spaces` 495, `snap_assets` 1496), 16 sources, 20 table + 20 view models, 5 exposures, macros (`kwh_to_kgco2e`, `safe_divide`, `is_working_hours`, `uk_local_ts`). Gold covers P06 (`dim_space/building/department/date`, `fct_timetable_event`, `fct_space_observed_occupancy`), P07 (`fct_work_order`, `dim_asset/trade`, `mart_asset_health`), P08 (`fct_energy_daily`+HDD, `fct_meter_hh`, `dim_emission_factor`), P09 (`dim_inspection_type`, `fct_inspection`, `mart_compliance_status`), P10 (category map seed). DESNZ 2025 factors via `fetch_desnz.py` (electricity 0.177, gas 0.2027 kgCO2e/kWh), never typed.

**Measured:** `dbt build --full-refresh` ~15–19s: PASS=196 WARN=0 ERROR=0 (5 exposures, 1 incremental, 4 seeds, 2 snapshots, 147 data + 2 unit + 11 singular `assert_*`, 21/21 marts contracted, 41/41 models tested, 292/292 cols documented). Silver→mart reconciliation fully explained (e.g. space 495→495 Δ0, meter HH 68119→67822 Δ-297 defect meters, timetable 12347→12026 Δ-321 quarantined/future, sensors 773974→773974, cafm 4171→4171). `sqlfluff` clean, `dbt docs generate` OK. Fixes: space-ID grain via truth join, TZ-correct `AT TIME ZONE 'UTC'` date casts, `assert_asset_life_sane` rewrite, unit-test YAML placement, AM04 `SELECT *` expansion.

**Show it:** `platform/dbt/README.md`, `ACCEPTANCE_P04.md` §4 table, `target/catalog.json`.

## P05 — CI/CD (`.github/workflows/`)

**Problem:** every push proves lint+type+test+build+DQ still green.

**Built:** `ci.yml` (ruff, mypy, pytest ≥80%, small data→ingest→reconcile→`dbt build`→DQ gate→sqlfluff→terraform fmt/validate→tflint→compose config→Airflow hook→mkdocs strict, matrix 3.11/3.12), `nightly.yml` (full profile + dbt-docs + issue-on-fail), `docs.yml` (Pages), `release.yml` (tag `v*` dists + changelog), `security.yml` (pip-audit, gitleaks, CodeQL), `_reusable.yml`, dependabot, pre-commit mirror, PR template, CODEOWNERS placeholder, `branch-protection.md`, `ci-demo.md`, `CONTRIBUTING.md`, `Makefile` targets.

**Measured locally:** ruff clean (70 files), mypy clean 24 files, pytest 27 passed, `dbt build` PASS=183, `dq_gate.py` exit 0 (fabricated error fixture → exit 1), sqlfluff exit 0, compose config exit 0, mkdocs strict green, wall ~4min (<10min CI). Human to-dos: push, enable Pages/protection, link first green run.

## P06 — Space utilisation (`projects/p06-space-utilisation/`)

**Problem:** which rooms are booked but empty, space per person by dept, what could be released.

**Built:** `src/utilisation.py` (freq, occ, util=freq×occ, no-show, mismatch) + `tests/test_utilisation.py` (incl. 1-room-3-events acceptance) + `validation/v01–v05.sql` (KPIs, heatmap, allocation, B003 check, DST-safe sensor→event join over 249k readings) + `powerbi/` handoff (`model.md`, `queries/*.pq` 7 files, `measures.dax`, `wireframe.md`, `theme.json`, `build-guide.md`) + `streamlit_app.py` mirror + `methodology.md`, `docs/findings.md`.

**Measured (small seed 42):** 495 spaces, 24,052 booked hrs: frequency 8.4%, occupancy 15.7%, utilisation 4.2%. B003 booked ~55% but ~21% full (0 rooms ≥70%, all 30 <30% — weaker than spec, reported as measured). D-ENG 247.5 m²/staff-FTE vs 64.3 median (+285% measured vs spec ~40%). 3 no-shows / 3,336 covered (~0%), 6,704 capacity mismatches (56%) — the actionable story. Coverage gaps quantified (28% sensor coverage, 222 invalid).

## P08 — Net zero & carbon (`projects/p08-net-zero-carbon/`)

**Problem:** are we on net-zero pathway, who drives emissions, where is out-of-hours waste.

**Built:** `src/carbon.py` (scopes, intensity, HDD, pathway variance, baseload) + `tests/test_carbon.py` (7 tests incl. 1-meter-1-month) + `validation/v01–v04.sql` (scope totals, intensity, baseload, summer gas) + `scripts/export_gold.py` + `powerbi/` handoff (5 queries, measures, wireframe, guide) + `streamlit_app.py` + `methodology.md` (GHG Protocol scopes, DESNZ provenance, HDD limits, market-based placeholder never mixed).

**Measured:** Scope 1 258,943 kWh → 52,488 kgCO2e; Scope 2 609,043 kWh → 107,801 kgCO2e. B007 tops intensity 1.9872 kgCO2e/m² and baseload 48.8% peak (planted #1 confirmed). B019 summer heating not verifiable on small (no B019/summer — exact default filters documented, not assumed). No dbt models added (uses existing marts); mart baselines NULL so pathway uses user baseline param.

## P02 — Airflow (in-progress, `p02-orchestration` branch)

**Built so far (964 insertions, 15 files):** `tasks/pipeline.py` (257 lines, airflow-free: landing list, header/drift check vs `platform/contracts/`, quarantine move, bronze+re-silver idempotent, watermarks, `ops.pipeline_runs` DuckDB store, Mailpit alerts never-raise, `run_dbt_build`, `dq_checkpoint` P03 hook, `publish_gold` 16 tables, `housekeeping` archive/prune) + `tasks/callbacks.py` + 7 DAGs (`ingest_space_register`, `ingest_cafm_workorders`, `ingest_meter_hh`, `ingest_bms_trends`, `transform_and_test` incl. asset-triggered dbt, `dq_report_daily`, `housekeeping`) + `dags/common.py` + tests (`test_task_funcs` 125 lines, `test_dag_contract`, `test_dagbag` airflow-gated).

**Show when merged:** `docker compose` Airflow + Mailpit, watermark re-runs, ops DB history, gold publish.

## P03 — Data quality (in-progress, `master`)

**Built so far:** 133 YAML checks across 10 datasets (`spaces`, `assets`, `work_orders`, `inspections`, `timetable`, `meters_a/b`, `sensors`, `bms`, `snapshots`) + engines: `spec.py`, `gxcompile.py`→GX suites, `gxrun.py`, `sqlchecks.py` (DuckDB for high-volume/stats GX cannot express), `store.py` (`data/quality.duckdb` `dq.results/failed_rows/scores/runs/alerts` + gold parquet/csv), `recall.py` (355 lines, ground-truth×quarantine mapping per defect injection order), `scoring.py` (weighted error=3/warn=2/info=1), `alerts.py` (>5pt drop or error fail), `run.py`, `cli.py`. GX 1.23.2 API verified empirically (`PLAN_P03.md`), perf 4×774k rows ~2s, heavy tables to SQL engine.

**Remaining:** trend (12 snapshots), GX Data Docs, `dq-policy.md`, Power BI scorecard handoff, clean-run + coverage gates, acceptance doc + STATUS tick.

---

## How to showcase (for hiring panel)

1. Lead with diagrams: `docs/DATA_MODEL.md`, `platform/README.md`, `projects/p06/README.md §2`, `projects/p08/README.md §2`.
2. Numbers above are measured — quote them with profile/seed/date. Foot every chart “Synthetic data — no real performance implied.”
3. Live demo without Power BI: `streamlit run projects/p06-space-utilisation/streamlit_app.py`, `.../p08-...`.
4. Power BI build is 1–3h human: `powerbi/model.md` → `queries/*.pq` → `measures.dax` → `wireframe.md` → `build-guide.md` validation checklist (SQL in `validation/` ties out).
5. Honest gaps to state: P01 dates §11, P04 default-profile runtime unmeasured, P08 single-quarter/HDD weak + single factor year, P06 attendance proxies need registers, P05 Pages/protection human step.
6. Skills map: E2/E4 pipelines+integration (P01/P02/P04), E5 analytics (P06/P08), E6 testing (all), D3 quality (P03), D5 Power BI handoff (P06/P08), D7 standards provenance (DESNZ/GHG in `DATA.md`), D8 sustainability (P08).

## Reproduce

```bash
make setup
make data PROFILE=small
make ingest
make dbt-build
make p06-run
make p08-run
make test
make lint
```
