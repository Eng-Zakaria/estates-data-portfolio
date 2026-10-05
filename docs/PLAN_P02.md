# PLAN: P02 Orchestrated ETL (Airflow 3.3.1) — branch p02-orchestration

## Goal
Orchestrate P01 ingest + P04 dbt in Airflow (sensors, dynamic mapping,
idempotent reruns/backfills, drift quarantine, ops store + Mailpit alerts,
runbook, ADR). All synthetic. Work happens on branch `p02-orchestration`
after the 2026-10-05 worktree wipe: commit early, merge only on user go-ahead.

## API verification (empirical, 2026-10-06, NOT from memory)
- Official compose `.../apache-airflow/3.3.1/docker-compose.yaml` (CeleryExecutor,
  Postgres, Redis, image `apache/airflow:3.3.1`) — vendored with ASF header.
- `from airflow.sdk import DAG, Asset`; producer `outlets=[asset]`; consumer
  `schedule=[asset]`; `schedule="@daily"` (3.3.1 assets + asset-scheduling docs).
- `PythonOperator` at `airflow.providers.standard.operators.python`;
  `FileSensor` at `...standard.sensors.filesystem` (class in installed 1.18.0).
- Constraints `constraints-3.3.1/constraints-3.{11,12}.txt` fetched OK (CI install).
- Mailpit `axllent/mailpit:v1.31.4` (registry API, 2026-10-03).
- Compose quirk found: non-dot relative paths become named volumes →
  project dir is `platform/orchestration`, `AIRFLOW_PROJ_DIR=.`.
- Local airflow import broken on Windows → host runs pure-logic tests only.

## Tasks
1. tasks/ pure logic ✅ committed; 7 DAGs ✅ committed; tests ✅ (9 pass, 3 skip).
2. Container stack ✅ committed; compose config valid.
3. Makefile targets ✅ committed; docs (runbook/ADR/README/this plan) this batch.
4. Build image → up → pools → DagBag in-container → demo good/corrupt →
   backfill 30 d → export ops CSV → UI/Mailpit screenshots (human fills .png).
5. CI hook: constraints airflow install in `.github/workflows/ci.yml` (shared edit last).
6. `docs/ACCEPTANCE_P02.md`, STATUS tick (on branch), final ruff/pytest, merge note.

## Risks
- Image build + stack bring-up time on Docker Desktop; custom-image pip
  install is the long pole (background it).
- Other sessions own shared files → NEW files only until final step.
- `data/landing`, `data/*.duckdb` are gitignored; demo artefacts stay local
  except the exported CSV + docs.
