"""Weekly housekeeping: archive landed files, prune ops history.

Retention: landing files older than 30 days move to lake/archive/;
ops.pipeline_runs keeps 90 days. Bronze partitions follow the same policy
once partitioning by ingest_date rolls over (documented, not yet enforced).
"""

from __future__ import annotations

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from common import COMMON_TAGS, DEFAULT_ARGS, MAX_ACTIVE_RUNS, OWNER
from tasks.pipeline import housekeeping


def _housekeep(**context) -> dict:
    return housekeeping()


with DAG(
    dag_id="housekeeping",
    schedule="@weekly",
    catchup=False,
    max_active_runs=MAX_ACTIVE_RUNS,
    default_args=DEFAULT_ARGS,
    tags=COMMON_TAGS + ["ops"],
    doc_md=__doc__,
) as dag:
    clean = PythonOperator(task_id="archive_and_prune", python_callable=_housekeep)
