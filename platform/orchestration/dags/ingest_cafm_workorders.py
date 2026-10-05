"""Hourly CAFM work-order ingest: watermark incremental, idempotent upsert.

Only files not seen in the watermark are processed; P01 bronze checksums make
reruns safe even if the watermark lags.
"""

from __future__ import annotations

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import Asset, DAG

from common import COMMON_TAGS, DEFAULT_ARGS, MAX_ACTIVE_RUNS, OWNER
from tasks.pipeline import (
    check_schema_drift,
    ingest_file,
    load_watermark,
    new_files_since,
    quarantine_landing_file,
    save_watermark,
    send_alert,
)

SOURCE = "cafm_workorders"
SILVER_ASSET = Asset("estates/silver/cafm_workorders")


def _list_new(**context) -> list[dict]:
    watermark = load_watermark(SOURCE)
    return [{"file": f} for f in new_files_since(SOURCE, watermark)]


def _ingest_one(path: str) -> dict:
    drift = check_schema_drift(SOURCE, path)
    if drift.get("drift") or drift.get("error"):
        dest = quarantine_landing_file(SOURCE, path, f"schema drift: {drift}")
        send_alert(f"{SOURCE} schema drift quarantined",
                   f"file={path}\nquarantined_to={dest}\ndrift={drift}")
        return {"status": "quarantined", "file": path}
    return ingest_file(SOURCE, path)


def _ingest_all(**context) -> dict:
    ti = context["ti"]
    items = ti.xcom_pull(task_ids="list_new_files") or []
    results = [_ingest_one(item["file"]) for item in items]
    watermark = load_watermark(SOURCE)
    seen = set(watermark.get("files", [])) | {item["file"] for item in items}
    watermark["files"] = sorted(seen)
    watermark["last_processed"] = items[-1]["file"] if items else watermark.get("last_processed")
    save_watermark(SOURCE, watermark)
    return {"status": "ok", "files": len(items), "results": results}


with DAG(
    dag_id="ingest_cafm_workorders",
    schedule="@hourly",
    catchup=False,
    max_active_runs=MAX_ACTIVE_RUNS,
    default_args=DEFAULT_ARGS,
    tags=COMMON_TAGS + ["cafm"],
    owner=OWNER,
    doc_md=__doc__,
) as dag:
    list_new = PythonOperator(task_id="list_new_files", python_callable=_list_new)

    ingest = PythonOperator(
        task_id="bronze_silver_watermarked",
        python_callable=_ingest_all,
        outlets=[SILVER_ASSET],
    )

    list_new >> ingest
