# P02 runbook (synthetic demo stack)

## Quick commands

```bash
make airflow-up      # build image, initdb, create pools, start stack
make airflow-ps      # container status
make airflow-logs    # follow scheduler logs
make airflow-down    # stop (keeps data); volumes hold Postgres + logs
```

UI: http://localhost:8080 (`airflow` / DEMO ONLY password in
`platform/orchestration/.env`). Mailpit UI: http://localhost:8025.

## When a DAG fails

1. **Read the alert mail** (Mailpit): dag, task, run, interval, error tail.
2. **Open the task log** in the Airflow UI (or
   `platform/orchestration/logs/dag_id=<...>/`).
3. **Check `ops.pipeline_runs`** for rows_in/out and the recorded error:
   `python platform/orchestration/scripts/export_runs.py`.
4. **Common causes and fixes:**

| Symptom | Likely cause | Fix |
|---|---|---|
| `wait_for_landing_file` keeps poking | supplier file not dropped yet | drop via `scripts/demo_drop.py`; sensor timeout is 6 h then it fails loudly |
| `schema_drift_check` → quarantined | supplier renamed/added columns | inspect `data/lakehouse/quarantine_files/<source>/`; update contract + P01 silver mapping, re-drop file |
| `bronze_silver*` fails | corrupt file passed drift (truncated rows) | file is checksum-skipped on retry; fix supplier extract, re-drop |
| `dbt_build` fails | mart/test failure (see P04) | fix model, clear + rerun `transform_and_test` |
| `dq_checkpoint` fails | error-severity DQ fail (P03) | triage via DQ scorecard, rerun |
| callback mail missing | Mailpit down | restart stack; callbacks never fail the task |

5. **Rerun**: clear the failed task in the UI (or
   `airflow dags clear <dag> ...`). Bronze checksums make re-ingest a no-op
   for already-loaded files; silver rewrites deterministically.

## Backfill

```bash
make airflow-backfill   # 30-day ingest_meter_hh backfill + ops CSV export
```

Idempotent by checksum; reruns change nothing.

## Adding a new source

1. Add landing glob to `SOURCE_FILE_PATTERNS` in `tasks/pipeline.py`.
2. Add contract `platform/contracts/<source>.yml` (P01).
3. Copy `dags/ingest_bms_trends.py` → new DAG file (mapped ingest fits most sources).
4. Add `Asset("estates/silver/<source>")` outlet + include it in
   `transform_and_test` schedule list if marts need it.
5. Add unit tests in `tests/test_task_funcs.py`; run `pytest`; update this runbook.
