"""P03 tests: recall rules on hand-built quarantine/defect fixtures."""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest
from quality import recall
from quality.spec import CheckSpec


def _recall_spec(**overrides):
    doc = {
        "id": "t_recall",
        "dataset": "work_orders",
        "dimension": "reconciliation",
        "severity": "error",
        "threshold": 100.0,
        "owner": "data-platform",
        "description": "d",
        "why_it_matters": "w",
        "engine": "recall",
        "kwargs": {"table": "cafm_workorders", "defect_type": "duplicate_rows"},
    }
    doc.update(overrides)
    return CheckSpec(**doc)


@pytest.fixture()
def con():
    c = duckdb.connect()
    c.register(
        "defects_df",
        pd.DataFrame(
            [
                ("cafm_workorders", "duplicate_rows", "WO-1"),
                ("cafm_workorders", "duplicate_rows", "WO-2"),
                ("cafm_workorders", "duplicate_rows", "WO-3"),
                ("cafm_workorders", "orphan_fk", "B999-ORPHAN"),
                ("timetable", "misspelt_category", "EV-00001xx"),
                ("timetable", "misspelt_category", "EV-00002xx"),
                ("space_register", "nulls_in_mandatory", "None"),
                ("space_register", "nulls_in_mandatory", "blank"),
                ("bms_trends", "nulls_in_mandatory", "N/A-strings"),
            ],
            columns=["tbl", "type", "row_key"],
        ),
    )
    c.execute('CREATE VIEW defects AS SELECT tbl AS "table", type, row_key FROM defects_df')
    c.register(
        "quarantine_work_orders",
        pd.DataFrame(
            [("WO-1", "duplicate:WO_Number"), ("WO-2", "nulls_in_mandatory")],
            columns=["WO_Number", "_reject_reason"],
        ),
    )
    c.register(
        "quarantine_timetable",
        pd.DataFrame(
            [("EV-9", "duplicate:event_id")],
            columns=["event_id", "_reject_reason"],
        ),
    )
    c.register(
        "quarantine_spaces",
        pd.DataFrame(
            [("R1", "nulls_in_mandatory"), ("R2", "nulls_in_mandatory")],
            columns=["Room", "_reject_reason"],
        ),
    )
    c.register(
        "quarantine_bms",
        pd.DataFrame(
            [("P1", "2026-01-01", "nulls_in_mandatory:N/A")],
            columns=["point", "ts", "_reject_reason"],
        ),
    )
    c.register(
        "silver_timetable",
        pd.DataFrame(
            [("EV-00001xx",), ("EV-00002xx",)],
            columns=["event_id"],
        ),
    )
    return c


def _specs_with_leak():
    leak = CheckSpec(
        id="tt_event_id_pattern",
        dataset="timetable",
        dimension="validity",
        severity="error",
        threshold=100.0,
        owner="x",
        description="d",
        why_it_matters="w",
        engine="gx",
        expectation="ExpectColumnValuesToMatchRegex",
        kwargs={"column": "event_id", "regex": "^EV-[0-9]+$"},
        key_col="event_id",
    )
    return {"tt_event_id_pattern": leak}


def test_exact_keys_overlap_safe(con):
    spec = _recall_spec()
    res = recall.evaluate(con, spec, {}, {}, lake="nope")
    # WO-1, WO-2 in quarantine (any reason); WO-3 missing
    assert (res.planted, res.detected) == (3, 2)
    assert res.rows_failed == 1
    assert res.samples == [{"row_key": "WO-3"}]


def test_exact_keys_with_leak_union(con):
    spec = _recall_spec(
        id="t2",
        kwargs={"table": "timetable", "defect_type": "future_dates"},
    )
    c2 = duckdb.connect()
    c2.register(
        "defects_df",
        pd.DataFrame(
            [("timetable", "future_dates", "EV-1"), ("timetable", "future_dates", "EV-2")],
            columns=["tbl", "type", "row_key"],
        ),
    )
    c2.execute('CREATE VIEW defects AS SELECT tbl AS "table", type, row_key FROM defects_df')
    c2.register(
        "quarantine_timetable",
        pd.DataFrame([("EV-1", "nulls_in_mandatory")], columns=["event_id", "_reject_reason"]),
    )
    c2.register("silver_timetable", pd.DataFrame([], columns=["event_id"]))
    from quality.spec import CheckSpec

    leak_spec = CheckSpec(
        id="tt_no_future_date",
        dataset="timetable",
        dimension="validity",
        severity="error",
        threshold=100.0,
        owner="estates-analytics",
        description="d",
        why_it_matters="w",
        engine="gx",
        expectation="ExpectTableRowCountToBeBetween",
        kwargs={"min_value": 0},
        key_col="event_id",
    )
    res = recall.evaluate(
        c2, spec, {"tt_no_future_date": leak_spec}, {"tt_no_future_date": [{"event_id": "EV-2"}]}, lake="nope"
    )
    assert (res.planted, res.detected) == (2, 2)


def test_masked_count_rule(con):
    spec = _recall_spec(id="t3", kwargs={"table": "timetable", "defect_type": "misspelt_category"})
    res = recall.evaluate(
        con,
        spec,
        _specs_with_leak(),
        {"tt_event_id_pattern": [{"event_id": "EV-00001xx"}, {"event_id": "EV-00002xx"}]},
        lake="nope",
    )
    assert (res.planted, res.detected) == (2, 2)


def test_space_nulls_blank_rule(con):
    spec = _recall_spec(id="t4", kwargs={"table": "space_register", "defect_type": "nulls_in_mandatory"})
    c2 = duckdb.connect()
    c2.execute(
        'CREATE VIEW defects AS SELECT tbl AS "table", type, row_key FROM ('
        "SELECT 'space_register' AS tbl, 'nulls_in_mandatory' AS type, 'blank' AS row_key)"
    )
    c2.register(
        "quarantine_spaces",
        pd.DataFrame([("R1", "nulls_in_mandatory")], columns=["Room", "_reject_reason"]),
    )
    import pathlib
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        bronze = pathlib.Path(tmp) / "bronze" / "space_register" / "x"
        bronze.mkdir(parents=True)
        pd.DataFrame([{"Room": "R1", "building_name": "B"}]).to_parquet(bronze / "a.parquet")
        res = recall.evaluate(c2, spec, {}, {}, lake=tmp)
        # 1 planted (blank), blank absent from bronze -> detected
        assert (res.planted, res.detected) == (1, 1)


def test_bms_aggregate_rule(con):
    spec = _recall_spec(id="t5", kwargs={"table": "bms_trends", "defect_type": "nulls_in_mandatory"})
    res = recall.evaluate(con, spec, {}, {}, lake="nope")
    assert (res.planted, res.detected) == (1, 1)


def test_unknown_rule_raises():
    spec = _recall_spec(id="t6", kwargs={"table": "cafm_workorders", "defect_type": "nope"})
    c = duckdb.connect()
    c.register(
        "defects_df",
        pd.DataFrame(
            [("cafm_workorders", "nope", "WO-1")],
            columns=["tbl", "type", "row_key"],
        ),
    )
    c.execute('CREATE VIEW defects AS SELECT tbl AS "table", type, row_key FROM defects_df')
    with pytest.raises(ValueError, match="no recall rule"):
        recall.evaluate(c, spec, {}, {}, lake="nope")
