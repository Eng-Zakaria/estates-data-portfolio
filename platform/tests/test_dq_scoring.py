"""P03 tests: scoring formulas and alert logic."""

from __future__ import annotations

import duckdb
import pytest
from quality import alerts, scoring
from quality.scoring import CheckOutcome


def _spec(severity="error", key=""):
    return scoring.CheckSpec(
        id="t",
        dataset="ds",
        dimension="validity",
        severity=severity,
        threshold=100.0,
        owner="x",
        description="d",
        why_it_matters="w",
        engine="sql",
        sql_checked="SELECT 1",
        sql_failed="SELECT 1",
    )


def _outcome(
    check_id="t", dataset="ds", dimension="validity", severity="error", pass_rate=1.0, threshold=100.0, by_building=None
):
    return CheckOutcome(check_id, dataset, dimension, severity, pass_rate, threshold, by_building)


def test_dataset_score_perfect():
    specs = {"a": _spec("error"), "b": _spec("warn")}
    outcomes = {"a": _outcome("a", pass_rate=1.0), "b": _outcome("b", pass_rate=1.0)}
    scores = scoring.dataset_scores(specs, outcomes)
    assert scores["ds"][0] == pytest.approx(100.0)
    assert scores["ds"][1] == 2


def test_dataset_score_partial():
    specs = {"a": _spec("error"), "b": _spec("warn")}
    outcomes = {"a": _outcome("a", pass_rate=0.5), "b": _outcome("b", pass_rate=1.0)}
    scores = scoring.dataset_scores(specs, outcomes)
    # error weight=3, warn weight=2: (3*50 + 2*100) / 5 = 350/5 = 70
    assert scores["ds"][0] == pytest.approx(70.0)


def test_dataset_score_empty():
    assert scoring.dataset_scores({}, {}) == {}


def test_dimension_scores():
    specs = {
        "a": _spec("error").model_copy(update={"dimension": "validity"}),
        "b": _spec("warn").model_copy(update={"dimension": "uniqueness"}),
    }
    outcomes = {
        "a": _outcome("a", pass_rate=0.8, dimension="validity"),
        "b": _outcome("b", pass_rate=0.6, dimension="uniqueness"),
    }
    scores = scoring.dimension_scores(specs, outcomes)
    assert ("ds", "validity") in scores
    assert ("ds", "uniqueness") in scores
    assert scores[("ds", "validity")][0] == pytest.approx(80.0)
    assert scores[("ds", "uniqueness")][0] == pytest.approx(60.0)


def test_building_scores():
    specs = {"a": _spec("error")}
    outcomes = {
        "a": _outcome(
            "a",
            by_building={
                "B1": {"checked": 10, "failed": 1},
                "B2": {"checked": 10, "failed": 0},
            },
        )
    }
    scores = scoring.building_scores(specs, outcomes)
    assert scores["B1"][0] == pytest.approx(90.0)
    assert scores["B2"][0] == pytest.approx(100.0)


def test_alert_error_fail():
    con = duckdb.connect()
    con.execute("CREATE SCHEMA dq")
    con.execute("CREATE TABLE dq.alerts (run_id VARCHAR, alert_kind VARCHAR, dataset VARCHAR, detail VARCHAR)")
    con.execute(
        "CREATE TABLE dq.scores (run_id VARCHAR, grain VARCHAR, dataset VARCHAR,"
        " key VARCHAR, score DOUBLE, n_checks BIGINT)"
    )
    raised = alerts.evaluate_alerts(con, "r1", {"ds": 95.0}, [("chk1", "ds")])
    assert len(raised) == 1
    assert raised[0][0] == "error_fail"
    rows = con.execute("SELECT alert_kind, dataset, detail FROM dq.alerts").fetchall()
    assert rows[0][0] == "error_fail"
    assert rows[0][1] == "ds"


def test_alert_score_drop():
    con = duckdb.connect()
    con.execute("CREATE SCHEMA dq")
    con.execute("CREATE TABLE dq.alerts (run_id VARCHAR, alert_kind VARCHAR, dataset VARCHAR, detail VARCHAR)")
    con.execute(
        "CREATE TABLE dq.scores (run_id VARCHAR, grain VARCHAR, dataset VARCHAR,"
        " key VARCHAR, score DOUBLE, n_checks BIGINT)"
    )
    # seed trailing mean above current
    for i, s in enumerate([90, 92, 88, 91, 89, 90, 90]):
        con.execute("INSERT INTO dq.scores VALUES (?, 'dataset', 'ds', '', ?, 1)", [f"r{i}", s])
    raised = alerts.evaluate_alerts(con, "r8", {"ds": 80.0}, [])
    assert any(k == "score_drop" for k, _, _ in raised)


def test_alert_no_score_drop_when_above_threshold():
    con = duckdb.connect()
    con.execute("CREATE SCHEMA dq")
    con.execute("CREATE TABLE dq.alerts (run_id VARCHAR, alert_kind VARCHAR, dataset VARCHAR, detail VARCHAR)")
    con.execute(
        "CREATE TABLE dq.scores (run_id VARCHAR, grain VARCHAR, dataset VARCHAR,"
        " key VARCHAR, score DOUBLE, n_checks BIGINT)"
    )
    for i, s in enumerate([90, 92, 88, 91, 89, 90, 90]):
        con.execute("INSERT INTO dq.scores VALUES (?, 'dataset', 'ds', '', ?, 1)", [f"r{i}", s])
    raised = alerts.evaluate_alerts(con, "r8", {"ds": 88.0}, [])
    assert not any(k == "score_drop" for k, _, _ in raised)
