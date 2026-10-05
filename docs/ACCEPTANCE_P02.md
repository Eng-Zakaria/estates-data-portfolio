# ACCEPTANCE P02 — Orchestrated ETL (Airflow 3.3.1) (branch p02-orchestration)

> Synthetic data throughout. No real university/building data implied.

## Delivered (branch commits)

| Commit | Scope |
|---|---|
| `d775772` | feat: P02 pure task logic (ingest, drift, watermark, ops store, alerts) |
| `f1a7f2d` | feat: P02 seven DAGs (sensors, mapping, asset-triggered dbt) |
| `4be7fae` | test: P02 task-func units + DagBag/contract tests (airflow-gated) |
| `c93ec25` | feat: P02 container stack (official 3.3.1 compose, custom image, mailpit, demo scripts) |
| `09da07c` | feat: P02 make targets (airflow build/up/down/backfill) |
| `ac93011` | docs: P02 runbook, ADR-002, README and plan |
| `de3de73` | style: P02 ruff autofix (import order, datetime.UTC) |
| `...` | fix: build context / .env encoding / image install without constraints |

## Local verification (small profile, seed 42)

| Check | Result |
|---|---|
| `ruff check platform/orchestration` + `ruff format --check` | clean (19 files) |
| `pytest platform/orchestration/tests/` | 9 passed, 3 skipped (airflow-gated) |
| `docker compose ... config --quiet` | exit 0 (project dir = platform/orchestration) |
| Image build | in progress (no-constraints install, pinned 3.3.1) |

## Acceptance mapping

- **`make airflow-up` starts the stack; UI reachable; DAGs listed without import errors** — compose config validated; custom image builds P01/P04 deps; Mailpit healthcheck + `fs_landing` conn defined; pools created by `airflow-up` target.
- **Demo script: good file → pipeline runs green; corrupt file → alert in Mailpit, file quarantined, other DAGs unaffected** — `scripts/demo_drop.py --scenario both` stages both files; `ingest_space_register` FileSensor + drift check quarantines corrupt; `ingest_cafm_workorders` watermarks incremental; `ingest_meter_hh` / `ingest_bms_trends` dynamic mapping; all callbacks write `ops.pipeline_runs` + send to Mailpit (non-fatal).
- **30-day backfill completes; run history exported to `docs/pipeline_runs.csv` and UI screenshot placeholder `docs/img/airflow_runs.png`** — `make airflow-backfill` runs `ingest_meter_hh` backfill 2026-02-01..2026-03-02 + `export_runs.py` CSV; human adds UI screenshot.
- **Runbook + ADR + README** — `platform/orchestration/docs/runbook.md`, `docs/adr/002-orchestrator-choice.md`, `platform/orchestration/README.md` with skills mapping.

## Deviation from spec

- **DagBag test in CI** installs pinned airflow via constraints (`constraints-3.3.1/constraints-{3.11,3.12}.txt`) rather than running the full compose in CI — heavier but more reliable; full stack bring-up is `make airflow-up` locally and documented in runbook.
- **Image install drops `--constraint`** (constraints only apply to the `apache-airflow` install step itself per the official docs); pinned `apache-airflow==3.3.1` in requirements prevents up/downgrade.
- **Project directory is `platform/orchestration`** (not repo root) so relative binds `${AIRFLOW_PROJ_DIR:-.}/dags` resolve; `AIRFLOW_PROJ_DIR=.` + `--project-directory platform/orchestration` in Makefile.
- **Windows host cannot run Airflow** (POSIX-only) — all DAG/operator tests run inside containers or on CI Linux; host runs pure-logic task tests only (9 passing).

## Open for human merge

- Build finishes → `make airflow-up` → drop demo files → verify all 7 DAGs green → backfill → export runs → screenshot placeholders.
- Merge `p02-orchestration` → `main` on user go-ahead (other sessions may have moved `main`).
- STATUS tick only on merge.