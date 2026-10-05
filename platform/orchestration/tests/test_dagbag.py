"""P02 DagBag import test: zero import errors (runs in CI/Linux; host-safe skip).

CI invokes exactly this file when platform/orchestration/dags exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    from airflow.models import DagBag

    _HAS_WORKING_AIRFLOW = True
except Exception:
    _HAS_WORKING_AIRFLOW = False

pytestmark = pytest.mark.skipif(
    not _HAS_WORKING_AIRFLOW,
    reason="airflow runs on Linux (CI/compose); this host import is broken/unsupported",
)


def test_dagbag_no_import_errors():
    dag_folder = str(Path(__file__).resolve().parents[1] / "dags")
    bag = DagBag(dag_folder=dag_folder, include_examples=False)
    assert not bag.import_errors, f"DAG import errors: {bag.import_errors}"
    assert len(bag.dags) >= 7, f"expected >=7 DAGs, found {sorted(bag.dags)}"
