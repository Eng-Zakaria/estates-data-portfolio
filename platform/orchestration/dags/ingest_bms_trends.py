"""Daily BMS trends ingest: dynamic task mapping, one task per trend file."""

from __future__ import annotations

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG, Asset
from common import COMMON_TAGS, DEFAULT_ARGS, MAX_ACTIVE_RUNS, OWNER
from tasks.pipeline import (
    LANDING,
    check_schema_drift,
    ingest_file,
    list_landing_files,
    quarantine_landing_file,
    send_alert,
)

SOURCE = "bms_trends"
SILVER_ASSET = Asset("estates/silver/bms_trends")


def _list_bms_files(**context) -> list[dict]:
    return [{"source": SOURCE, "file": p} for p in list_landing_files(SOURCE, LANDING)]


def _ingest_mapped(op_kwargs: dict | None = None, **context) -> dict:
    item = op_kwargs or {}
    source, path = item["source"], item["file"]
    drift = check_schema_drift(source, path)
    if drift.get("drift") or drift.get("error"):
        dest = quarantine_landing_file(source, path, f"schema drift: {drift}")
        send_alert(f"{source} schema drift quarantined", f"file={path}\nquarantined_to={dest}\ndrift={drift}")
        return {"status": "quarantined", "file": path}
    return ingest_file(source, path)


with DAG(
    dag_id="ingest_bms_trends",
    schedule="@daily",
    catchup=False,
    max_active_runs=MAX_ACTIVE_RUNS,
    default_args={**DEFAULT_ARGS, "pool": "ingest_pool"},
    tags=COMMON_TAGS + ["bms"],
    owner=OWNER,
    doc_md=__doc__,
) as dag:
    list_files = PythonOperator(task_id="list_bms_files", python_callable=_list_bms_files)

    ingest = PythonOperator.partial(
        task_id="bronze_silver_mapped",
        python_callable=_ingest_mapped,
        outlets=[SILVER_ASSET],
    ).expand(op_kwargs=list_files.output)

    list_files >> ingest
