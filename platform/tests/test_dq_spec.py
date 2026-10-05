"""P03 tests: check-spec loading, validation, and suite compiler."""

from __future__ import annotations

import duckdb
import pytest

from quality import gxcompile
from quality.spec import CheckSpec, load_checks

CHECKS_DIR = "platform/quality/checks"


def _base(**overrides):
    doc = {
        "id": "t_check",
        "dataset": "spaces",
        "dimension": "completeness",
        "severity": "error",
        "threshold": 100.0,
        "owner": "estates-analytics",
        "description": "d",
        "why_it_matters": "w",
        "engine": "gx",
        "expectation": "ExpectColumnValuesToNotBeNull",
        "kwargs": {"column": "room_code"},
    }
    doc.update(overrides)
    return doc


def test_load_all_checks_meets_minimum_and_coverage():
    specs = load_checks(CHECKS_DIR)
    assert len(specs) >= 60, f"only {len(specs)} checks"
    dims = {s.dimension for s in specs}
    assert dims == {
        "completeness",
        "uniqueness",
        "validity",
        "consistency",
        "timeliness",
        "referential_integrity",
        "reconciliation",
    }
    assert {s.severity for s in specs} >= {"error", "warn"}
    assert {s.engine for s in specs} == {"gx", "sql", "recall"}


def test_ids_unique_and_well_formed():
    specs = load_checks(CHECKS_DIR)
    ids = [s.id for s in specs]
    assert len(set(ids)) == len(ids)


def test_threshold_maps_to_mostly():
    assert CheckSpec(**_base(threshold=98.0)).mostly == pytest.approx(0.98)
    assert CheckSpec(**_base(threshold=100.0)).mostly == 1.0


def test_rejects_unknown_expectation():
    with pytest.raises(ValueError, match="unsupported GX expectation"):
        CheckSpec(**_base(expectation="ExpectColumnValuesToBeMagical"))


def test_rejects_unknown_kwarg():
    with pytest.raises(ValueError, match="unknown kwargs"):
        CheckSpec(
            **_base(
                expectation="ExpectColumnValuesToNotBeNull",
                kwargs={"column": "a", "bogus": 1},
            )
        )


def test_rejects_bad_threshold_and_id():
    with pytest.raises(ValueError):
        CheckSpec(**_base(threshold=101.0))
    with pytest.raises(ValueError):
        CheckSpec(**_base(id="Not Valid!"))


def test_sql_specs_need_queries():
    with pytest.raises(ValueError, match="needs sql_checked"):
        CheckSpec(**_base(engine="sql"))
    with pytest.raises(ValueError, match="needs sql_checked_by_building"):
        CheckSpec(
            **_base(
                engine="sql",
                sql_checked="SELECT 1",
                sql_failed="SELECT 1",
                by_building=True,
                building_col="building_id",
            )
        )


def test_check_index_rejects_ambiguous_pair():
    a = CheckSpec(**_base(id="t_a"))
    b = CheckSpec(**_base(id="t_b"))
    with pytest.raises(ValueError, match="ambiguous"):
        gxcompile.build_check_index([a, b])


def test_value_set_from_resolution():
    con = duckdb.connect()
    con.execute("CREATE VIEW truth_buildings AS SELECT 'B001' AS building_id UNION ALL SELECT 'B002'")
    spec = CheckSpec(
        **_base(
            expectation="ExpectColumnValuesToBeInSet",
            kwargs={
                "column": "building_id",
                "value_set_from": {"truth_table": "buildings", "column": "building_id"},
            },
        )
    )
    lookup = gxcompile.fetch_truth_lists(con, {("buildings", "building_id")})
    assert lookup == {"buildings": {"building_id": ["B001", "B002"]}}
    assert gxcompile.resolve_kwargs(spec, lookup) == {
        "column": "building_id",
        "value_set": ["B001", "B002"],
    }
    with pytest.raises(ValueError, match="needs truth_lookup"):
        gxcompile.resolve_kwargs(spec, None)
