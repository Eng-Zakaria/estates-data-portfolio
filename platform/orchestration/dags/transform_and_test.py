"""Asset-triggered transform: dbt build -> DQ checkpoint -> publish gold extracts.

Runs when all four silver assets have fresh events (asset-aware scheduling).
dbt failures block the publish step but never the source ingest DAGs.
"""

from __future__ import annotations

from datetime import timedelta

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import Asset, DAG

from common import COMMON_TAGS, DEFAULT_ARGS, MAX_ACTIVE_RUNS, OWNER
from tasks.pipeline import dq_checkpoint, publish_gold, run_dbt_build

SPACE = Asset("estates/silver/space_register")
CAFM = Asset("estates/silver/cafm_workorders")
METER = Asset("estates/silver/meter_hh")
BMS = Asset("estates/silver/bms_trends")


def _dbt(**context) -> dict:
    result = run_dbt_build()
    if result["returncode"] != 0:
        raise RuntimeError(f"dbt build failed (rc={result['returncode']}): {result['tail'][-500:]}")
    return result


def _dq(**context) -> dict:
    result = dq_checkpoint()
    if result.get("status") == "fail":
        raise RuntimeError(f"DQ checkpoint failed: {result.get('tail', '')[-500:]}")
    return result


def _publish(**context) -> dict:
    return publish_gold()


with DAG(
    dag_id="transform_and_test",
    schedule=[SPACE, CAFM, METER, BMS],
    catchup=False,
    max_active_runs=MAX_ACTIVE_RUNS,
    default_args={**DEFAULT_ARGS, "pool": "dbt_pool", "execution_timeout": timedelta(hours=1)},
    tags=COMMON_TAGS + ["dbt", "gold"],
    owner=OWNER,
    doc_md=__doc__,
) as dag:
    dbt = PythonOperator(task_id="dbt_build", python_callable=_dbt)
    dq = PythonOperator(task_id="dq_checkpoint", python_callable=_dq)
    publish = PythonOperator(task_id="publish_gold", python_callable=_publish)

    dbt >> dq >> publish
