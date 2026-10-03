# Platform projects P01-P05 (one flagship lakehouse)

These five share one codebase under `platform/` so the flagship repo tells one coherent story: **ingest → orchestrate → validate → transform → ship via CI**. Each still has its own README section, acceptance evidence and STATUS row.

Depends on: `00-foundation-campus-synth.md`.

---

## P01: Campus data warehouse (medallion lakehouse)

**Location:** `platform/ingest/`, `infra/terraform/`
**Criteria covered:** E2, E3, E4, D1, D5
**Goal:** ingest messy source-system exports into bronze → silver layers (typed, deduplicated, conformed), query locally with DuckDB and optionally on AWS (S3 + Glue + Athena). Gold marts are built by dbt in P04.
**Stack:** Python, DuckDB, PyArrow/Parquet, Pydantic v2 (data contracts), Typer, MinIO (S3-compatible, Docker), Terraform (optional AWS).

### Layers

| Layer | Content | Rules |
|---|---|---|
| bronze | raw files converted to Parquet, all columns as strings | never alter values; add audit columns `_ingest_id, _source_system, _source_file, _loaded_at, _row_number, _row_hash`; partition `source/ingest_date=YYYY-MM-DD` |
| silver | typed, trimmed, deduplicated, UTC timestamps, standard units and IDs | invalid rows go to `quarantine/<table>` with `_reject_reason` |
| gold | star-schema marts | produced by P04 (dbt); P01 documents the contract |

### Tasks

1. **Contracts.** One YAML/Pydantic contract per source (columns, types, nullability, allowed values, date-format candidates, units). Contracts drive both validation and the catalogue.
2. **Bronze loader** (`ingest bronze --source cafm --file ...`): read xlsx/csv/parquet, write Parquet, record in `bronze_manifest` (file, sha256, rows, status, ingest_id).
3. **Idempotency.** Same checksum → skipped. A corrected file with new checksum → new `ingest_id`; silver keeps the latest by business key. Tests for both.
4. **Silver transforms** (one module per source): normalise strings and case, parse dates with explicit format candidates (log which format matched), cast types, clean currency/area strings, map names to canonical IDs, dedupe by business key, split valid/quarantine.
5. **Meter half-hour handling:** local → UTC with correct DST handling (46/50-period days), wide→long reshape, cumulative register → interval conversion with rollover detection, gap flags (flag, never fabricate values).
6. **Reference tables:** space-category map, asset-type map, building-name crosswalk. Unmapped values go to an `unmapped_values` report with fuzzy-match suggestions (rapidfuzz).
7. **Storage abstraction:** `STORAGE=local|minio|s3` via environment (DuckDB `httpfs` or fsspec). `docker-compose.yml` provides MinIO.
8. **Catalogue:** generate `docs/catalogue.md` from the contracts (table, column, type, description, source system, nullability).
9. **Terraform (optional, not applied by default):** S3 bucket (versioned, SSE, public access blocked), Glue database + tables for silver/gold, Athena workgroup with scan-limit and results bucket, least-privilege IAM role, AWS Budget alarm. `make aws-plan`, `make aws-apply`, `make aws-destroy`. README has a clear **cost warning**; CI runs only `terraform fmt/validate` and `tflint`.
10. **Sample queries:** `queries/*.sql` that run on DuckDB, with a note on Athena dialect differences.
11. **Mermaid architecture diagram** and a lineage table (source file → bronze table → silver table).

### Acceptance

- `make data && make ingest` builds all bronze and silver tables from the small profile in < 2 min.
- Row-count reconciliation report: raw rows = bronze rows; silver + quarantine = bronze (per source), zero unexplained loss.
- Re-running ingest changes nothing (idempotent; test).
- Spring-forward and autumn-back days produce the correct number of unique UTC periods per meter (test).
- Every planted defect of the "invalid row" kind in `ground_truth.yaml` lands in quarantine with a sensible reason.
- Terraform validates; the README explains the AWS path and its cost controls.

**CV bullet:** *Built a medallion lakehouse (DuckDB/Parquet, S3-compatible, Terraform for AWS) ingesting five heterogeneous estates sources with data contracts, idempotent loads and quarantine; reconciled 100% of rows end-to-end.*

---

## P02: Orchestrated ETL with Airflow

**Location:** `platform/orchestration/`
**Criteria covered:** E2, E7, D2, D3 (monitoring)
**Depends on:** P01 (ingest functions), P04 (dbt build step; stub first, wire later)
**Stack:** Apache Airflow (pin a version; use the official docker-compose; verify import paths for the chosen major version), Postgres metadata DB, Mailpit (SMTP sink for alerts), dbt CLI.

### DAGs

| DAG | Schedule / trigger | Behaviour |
|---|---|---|
| `ingest_space_register` | daily + file sensor | wait for landing file → bronze → silver → quarantine report |
| `ingest_cafm_workorders` | hourly or daily | incremental via modified-since watermark; idempotent upsert |
| `ingest_meter_hh` | daily | dynamic task mapping, one task per meter file; late files handled |
| `ingest_bms_trends` | daily | as above |
| `transform_and_test` | asset/dataset-triggered when ingests complete | `dbt build` → DQ checkpoint (P03) → publish gold extracts |
| `dq_report_daily` | daily | summarise DQ results, email digest |
| `housekeeping` | weekly | archive landed files, prune old logs/bronze partitions per retention policy |

### Requirements

1. Idempotent tasks keyed on `data_interval_start`; reruns and backfills are safe. Demo: `backfill` of 30 days documented with output.
2. Retries with exponential backoff, timeouts, sensible `max_active_runs`, pools to limit concurrency.
3. Failure handling: callback writes to `ops.pipeline_runs` (dag, task, run_id, status, duration, rows_in/out, error) and sends an email to Mailpit. One failing source must not block others.
4. Schema-drift task: compares incoming columns to the contract; on drift, quarantine the file and alert, don't crash silently.
5. Every DAG has `doc_md`, owner, tags, and `on_failure_callback`.
6. Tests: `DagBag` import test (zero import errors), unit tests for task functions independent of Airflow, a test that every DAG has retries and docs.
7. `docs/runbook.md`: what to do when each DAG fails; how to rerun; how to add a new source.
8. `docs/adr/00X-orchestrator-choice.md` comparing Airflow vs NiFi vs Node-RED vs cron for this use (links to P15 where Node-RED is used for streaming).

### Acceptance

- `make airflow-up` starts the stack; UI reachable; DAGs listed without import errors.
- Demo script: drop a good file → pipeline runs green; drop a corrupted file → alert in Mailpit, file quarantined, other DAGs unaffected.
- 30-day backfill completes; run history exported to `docs/img/airflow_runs.png` (placeholder for human screenshot) and a CSV of `ops.pipeline_runs`.

**CV bullet:** *Orchestrated five ingestion pipelines in Airflow with sensors, dynamic task mapping, idempotent backfills, schema-drift detection and failure alerting; documented run-books.*

---

## P03: Data quality framework

**Location:** `platform/quality/`
**Criteria covered:** E6, E7, D3
**Stack:** Great Expectations Core (pin version; follow that version's docs), DuckDB, Pydantic, Typer, Jinja2.

### Design

Checks are declared in YAML (`checks/<dataset>.yml`) and compiled to GX expectation suites. Every check has: `id`, `dataset`, `dimension` (completeness / uniqueness / validity / consistency / timeliness / referential_integrity / reconciliation), `severity` (error / warn / info), `threshold` (min pass %), `owner`, `description`, `why_it_matters`.

### Required checks (≥ 60). Examples by dataset

- **spaces:** unique `space_id`; `nia_m2` > 0 and < 2,000; category in controlled list; sum of space NIA per building ≤ building GIA; capacity > 0 for teaching categories.
- **assets:** install_date ≤ today; condition_grade ∈ {A,B,C,D}; every `space_id` exists; expected_life within 1-60; serial unique within manufacturer+model.
- **work_orders:** completed ≥ raised; cost ≥ 0; PPM jobs have an asset; priority ∈ {P1..P4}; no duplicate (wo_id).
- **meters:** no negative kWh (except export meters); gaps ≤ N consecutive periods; flat-line (≥ 48 identical readings); spike > k× rolling median; units consistent; daily count = 48 (46/50 on DST days).
- **timeliness / volume:** latest reading < 36 h old; daily row count within ±3σ of the trailing 28-day mean.
- **cross-source:** building areas in space register vs BIM (hook for P11); asset counts per building in CAFM vs handover.

### Outputs

1. `dq.results` (run_id, ts, dataset, check_id, dimension, severity, rows_checked, rows_failed, pass_rate, status) and `dq.failed_rows` (up to 100 sample rows per check) in DuckDB/Parquet.
2. Weighted **DQ score** per dataset / building / dimension (weights in config).
3. **Trend:** run over the 12 weekly snapshots from `campus-synth snapshots` so the score visibly improves as defects fall.
4. GX Data Docs (HTML), published via CI to Pages.
5. Alerts: score drop > 5 points vs 7-day average, or any `error` check failing; write to `ops` table and print a digest.
6. `docs/dq-policy.md`: dimension definitions, severities, response times, who is notified.
7. Power BI handoff (see AGENTS.md) for a one-page **DQ scorecard**: score by dataset, trend, worst buildings, top failing checks, failed-row drill-through.

### Acceptance

- Every deterministic planted defect in `ground_truth.yaml` is detected (recall 100% for deterministic types); report recall per defect type.
- Zero `error` failures on the clean (defects = 0) data set (false-positive rate 0).
- Check runtime on the default profile documented (< 5 min target).
- Unit tests: each custom check has a pass fixture and a fail fixture.

**CV bullet:** *Designed a YAML-driven data quality framework (60+ checks across 7 dimensions) with scoring, trend monitoring and failed-row quarantine; detected 100% of seeded defects with zero false positives on clean data.*

---

## P04: dbt project

**Location:** `platform/dbt/`
**Criteria covered:** E2, E4, E6, E7, D3, D4
**Stack:** dbt-core + dbt-duckdb (pin versions), dbt_utils, dbt-expectations (or equivalent), sqlfluff.

### Model layers

- `staging/`: `stg_<source>__<entity>`: 1:1 with silver tables, renames only, materialised as views.
- `intermediate/`: `int_*`: joins and business logic (current-space view, cleaned meter HH, enriched work orders, asset age/life remaining).
- `marts/`: dims `dim_building, dim_space, dim_asset, dim_department, dim_meter, dim_date, dim_inspection_type, dim_emission_factor`; facts `fct_meter_hh, fct_energy_daily, fct_work_order, fct_inspection, fct_timetable_event, fct_sensor_15min`; and analysis marts `mart_space_utilisation, mart_asset_health, mart_carbon_monthly, mart_compliance_status, mart_dq_scorecard`.

### Required features

1. **Sources** with freshness checks.
2. **Seeds:** space-category map, academic calendar, **DESNZ conversion factors** (fetched from the official source by a script, never typed from memory; table has factor, unit, year, source URL).
3. **Snapshots (SCD2)** on spaces and assets (category and condition grade changes) to produce historical views.
4. **Incremental model** `fct_meter_hh` (`unique_key = [meter_id, ts_utc]`) with a late-arriving-data lookback window.
5. **Macros:** `kwh_to_kgco2e`, `uk_local_ts`, `is_working_hours`, `safe_divide`.
6. **Tests:** ≥ 80 (not_null, unique, relationships, accepted_values, expression_is_true, recency, plus singular tests for business rules). dbt unit tests for key logic where the dbt version supports them.
7. **Contracts** enforced on mart models (column names and types).
8. **Exposures** documenting each Power BI dashboard (P06-P10) and its upstream models.
9. **Docs:** descriptions for all models/columns, owners and `meta` tags, `dbt docs generate` published by CI, lineage screenshot placeholder.
10. **Style:** sqlfluff config, consistent naming, CTE-first SQL, no business logic in staging.

### Acceptance

- `dbt build` is green on the small and default profiles.
- Coverage report: % models with ≥ 1 test, % columns documented (targets 100% / ≥ 90%).
- Every gold table named in P06-P10 specs exists and has a contract.
- Row-count reconciliation between silver and marts documented.

**CV bullet:** *Modelled the estate in dbt (staging → intermediate → marts) with SCD2 snapshots, incremental half-hourly meter facts, 80+ tests, enforced contracts and published lineage docs.*

---

## P05: CI/CD for data

**Location:** `.github/workflows/`, `.pre-commit-config.yaml`, root config
**Criteria covered:** D4, E7
**Stack:** GitHub Actions, uv, ruff, mypy, sqlfluff, pytest, terraform, gitleaks, pip-audit.

### Workflows

- **`ci.yml`** (pull requests and main): cache uv; ruff lint + format check; mypy on shared packages; sqlfluff on dbt; pytest with coverage gate (≥ 80% core); generate small-profile data → `dbt build` → run DQ checkpoint → fail on any `error` severity; `terraform fmt -check`, `validate`, `tflint`; `docker compose config`; Airflow DagBag import test; `mkdocs build --strict`. Matrix on Python 3.11 and 3.12 for packages. Concurrency group cancels superseded runs.
- **`nightly.yml`:** full-profile run, upload DQ report and dbt docs as artifacts, create an issue if it fails.
- **`docs.yml`:** deploy MkDocs + dbt docs + GX Data Docs to GitHub Pages.
- **`release.yml`:** on tag `v*`: build packages, generate changelog from conventional commits, attach artifacts.
- **`security.yml`:** pip-audit, gitleaks, CodeQL; `dependabot.yml` for pip, docker, actions.
- **Reusable workflow** (`workflow_call`) shared by projects that need lint + test.

### Also deliver

`.pre-commit-config.yaml` mirroring CI; PR template with checklist (tests, docs, DQ impact, data-contract change?); CODEOWNERS; `CONTRIBUTING.md` (branching, conventional commits); `docs/branch-protection.md` (manual GitHub settings the human must apply); README badges.

### Acceptance

- Green CI on main (link in README).
- `docs/ci-demo.md` shows a deliberately failing PR (failing dbt test or DQ error) turning CI red, with the failing step; a fix turning it green. Branch names and screenshots are placeholders for the human.
- CI wall time < 10 minutes on the small profile; caching demonstrated.
- No secrets in history (gitleaks clean).

**CV bullet:** *Automated testing and deployment of the data platform with GitHub Actions: linting, unit tests, dbt build and data-quality gates on every pull request, plus nightly full-volume runs and automated docs.*
