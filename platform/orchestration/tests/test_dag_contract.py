"""P02 DAG contract: every DAG has retries, docs, owner, tags and callbacks."""

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

EXPECTED_DAGS = {
    "ingest_space_register",
    "ingest_cafm_workorders",
    "ingest_meter_hh",
    "ingest_bms_trends",
    "transform_and_test",
    "dq_report_daily",
    "housekeeping",
}


def _bag():
    return DagBag(
        dag_folder=str(Path(__file__).resolve().parents[1] / "dags"),
        include_examples=False,
    )


def test_expected_dags_present():
    bag = _bag()
    assert EXPECTED_DAGS <= set(bag.dags), f"missing: {EXPECTED_DAGS - set(bag.dags)}"


def test_every_dag_has_retries_docs_owner_tags_callbacks():
    bag = _bag()
    assert not bag.import_errors
    for dag_id, dag in bag.dags.items():
        assert dag.doc_md, f"{dag_id}: missing doc_md"
        assert dag.owner == "estates-data", f"{dag_id}: owner={dag.owner}"
        assert dag.tags, f"{dag_id}: no tags"
        assert dag.default_args.get("retries", 0) >= 1, f"{dag_id}: no retries"
        assert dag.default_args.get("on_failure_callback") is not None, f"{dag_id}: no failure callback"
        assert dag.max_active_runs is not None, f"{dag_id}: max_active_runs unset"
