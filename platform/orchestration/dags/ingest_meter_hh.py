"""Daily meter half-hour ingest: dynamic task mapping, one task per meter file.

Late files are handled naturally: every run sweeps the whole landing zone and
P01 checksums skip already-loaded files, so backfills and reruns are safe.
"""

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

SOURCES = ["meter_hh_supplierA", "meter_hh_supplierB"]
SILVER_ASSET = Asset("estates/silver/meter_hh")


def _list_meter_files(**context) -> list[dict]:
    items = []
    for source in SOURCES:
        for path in list_landing_files(source, LANDING):
            items.append({"source": source, "file": path})
    return items


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
    dag_id="ingest_meter_hh",
    schedule="@daily",
    catchup=False,
    max_active_runs=MAX_ACTIVE_RUNS,
    default_args={**DEFAULT_ARGS, "pool": "ingest_pool"},
    tags=COMMON_TAGS + ["meters"],
    owner=OWNER,
    doc_md=__doc__,
) as dag:
    list_files = PythonOperator(task_id="list_meter_files", python_callable=_list_meter_files)

    ingest = PythonOperator.partial(
        task_id="bronze_silver_mapped",
        python_callable=_ingest_mapped,
        outlets=[SILVER_ASSET],
    ).expand(op_kwargs=list_files.output)

    list_files >> ingest
