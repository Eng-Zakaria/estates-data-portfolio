"""Daily space-register ingest: wait for landing file, drift-check, bronze/silver.

Failure of this DAG never blocks the other source DAGs (separate DAGs per
source by design). Corrupt files are quarantined + alerted, not crashed on.
"""

from __future__ import annotations

from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.filesystem import FileSensor
from airflow.sdk import DAG, Asset
from common import COMMON_TAGS, DEFAULT_ARGS, MAX_ACTIVE_RUNS, OWNER
from tasks.pipeline import (
    LANDING,
    check_schema_drift,
    ingest_file,
    quarantine_landing_file,
    send_alert,
)

SOURCE = "space_register"
SILVER_ASSET = Asset("estates/silver/space_register")

LANDING_GLOB = "space_register_*.xlsx"


def _drift_check(**context) -> dict:
    import glob
    import os

    files = sorted(glob.glob(os.path.join(str(LANDING), LANDING_GLOB)))
    if not files:
        return {"status": "no_files"}
    report = check_schema_drift(SOURCE, files[0])
    if report.get("drift") or report.get("error"):
        dest = quarantine_landing_file(SOURCE, files[0], f"schema drift: {report}")
        send_alert(f"{SOURCE} schema drift quarantined", f"file={files[0]}\nquarantined_to={dest}\ndrift={report}")
        return {"status": "quarantined", "dest": dest, "drift": report}
    return {"status": "ok", "file": files[0], "drift": report}


def _ingest(**context) -> dict:
    import glob
    import os

    files = sorted(glob.glob(os.path.join(str(LANDING), LANDING_GLOB)))
    if not files:
        return {"status": "no_files"}
    return ingest_file(SOURCE, files[0])


with DAG(
    dag_id="ingest_space_register",
    schedule="@daily",
    catchup=False,
    max_active_runs=MAX_ACTIVE_RUNS,
    default_args=DEFAULT_ARGS,
    tags=COMMON_TAGS + ["space"],
    owner=OWNER,
    doc_md=__doc__,
) as dag:
    wait_for_file = FileSensor(
        task_id="wait_for_landing_file",
        filepath=LANDING_GLOB,
        fs_conn_id="fs_landing",
        poke_interval=60,
        timeout=6 * 3600,
        mode="reschedule",
    )

    drift_check = PythonOperator(task_id="schema_drift_check", python_callable=_drift_check)

    ingest = PythonOperator(
        task_id="bronze_silver",
        python_callable=_ingest,
        outlets=[SILVER_ASSET],
    )

    wait_for_file >> drift_check >> ingest
