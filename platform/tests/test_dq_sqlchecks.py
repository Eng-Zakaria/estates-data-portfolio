"""P03 tests: every SQL check runs against hand-built fixtures with hand-checked counts.

Each fixture table mixes passing and failing rows; the parametrized expectations
below were computed by hand from the fixture, so both paths are exercised.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from quality import sqlchecks
from quality.spec import CheckSpec, load_checks

WINDOW_END = "2026-04-01"


def _ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    c.register(
        "silver_spaces",
        pd.DataFrame(
            [
                # room, building, category, nia, capacity
                ("R1", "B1", "Teaching", 50.0, 30),  # pass
                ("R2", "B1", "Teaching", 40.0, 0),  # fail teaching capacity
                ("R3", "B2", "Office", 900.0, 4),  # fail gia (B2 gia 800)
                ("R4", "B2", "Office", 100.0, 4),  # fail gia (sum 1000 > 800)
            ],
            columns=["room_code", "building_id", "space_category", "nia_m2", "capacity_seats"],
        ),
    )
    c.register(
        "truth_buildings",
        pd.DataFrame([("B1", 1000.0), ("B2", 800.0)], columns=["building_id", "gia_m2"]),
    )
    c.register(
        "truth_assets",
        pd.DataFrame(
            [("A1", "B1", "2020-01-01"), ("A2", "B1", "2099-06-01")],
            columns=["asset_id", "building_id", "install_date"],
        ),
    )
    c.register(
        "silver_work_orders",
        pd.DataFrame(
            [
                # id, asset, type, raised, completed, cost, building
                ("WO-1", "A1", "PPM", _ts("2026-01-05"), _ts("2026-01-06"), 10.0, "B1"),
                ("WO-2", "A1", "PPM", _ts("2026-01-05"), _ts("2026-01-04"), 10.0, "B1"),  # chrono
                ("WO-3", None, "PPM", _ts("2026-01-05"), None, 10.0, "B1"),  # ppm asset
                ("WO-4", "A1", "Reactive", _ts("2099-01-01"), None, 10.0, "B1"),  # future
                ("WO-5", "A1", "Reactive", _ts("2026-01-02"), None, 10.0, "B1"),
                ("WO-6", "A1", "Reactive", _ts("2026-03-20"), None, 10.0, "B2"),  # open recent
                ("WO-7", "A1", "Reactive", _ts("2025-01-01"), None, 10.0, "B1"),  # open aged
            ],
            columns=["WO_Number", "AssetRef", "wo_type", "raised_ts", "completed_ts", "cost_gbp", "building_id"],
        ),
    )
    c.register(
        "silver_meters_a",
        pd.DataFrame(
            [
                ("M1", _ts("2026-03-31 10:00"), 5.0),  # fresh, known
                ("M1", _ts("2026-03-31 10:30"), 5.0),
                ("M9", _ts("2099-01-01 00:00"), 5.0),  # future
                ("MOLD", _ts("2026-01-01 00:00"), 5.0),  # stale only
            ],
            columns=["meter_id", "ts_utc", "value"],
        ),
    )
    c.register(
        "truth_meters",
        pd.DataFrame(
            [("M1", "B1"), ("MOLD", "B1")],
            columns=["meter_id", "building_id"],
        ),
    )
    c.register(
        "silver_timetable",
        pd.DataFrame(
            [
                ("EV-1", "S1", "2026-01-06", "09:00", "11:00"),  # pass
                ("EV-2", "S1", "2099-01-01", "09:00", "11:00"),  # future
                ("EV-3", "S1", "2026-01-06", "11:00", "09:00"),  # negative duration
            ],
            columns=["event_id", "space_id", "date", "t_start", "t_end"],
        ),
    )
    c.register(
        "silver_inspections",
        pd.DataFrame(
            [
                ("IN-1", "B1", "2026-01-10", "2026-01-12"),  # pass
                ("IN-2", "B1", None, None),  # open pass
                ("IN-3", "B1", "2026-01-10", "2025-01-01"),  # too early
            ],
            columns=["inspection_id", "building_id", "due_date", "completed_date"],
        ),
    )
    c.register(
        "silver_sensors",
        pd.DataFrame(
            [
                ("SN-1", _ts("2026-03-31 10:00"), 400.0),
                ("SN-9", _ts("2026-01-01 10:00"), 400.0),  # unknown + stale
            ],
            columns=["sensor_id", "ts_utc", "value"],
        ),
    )
    c.register("truth_sensors", pd.DataFrame([("SN-1",)], columns=["sensor_id"]))
    c.register(
        "silver_bms",
        pd.DataFrame(
            [
                ("P1", _ts("2026-03-30 10:00"), 1.0),
                ("P1", _ts("2026-03-30 10:00"), 1.0),  # dup pair
                ("P2", _ts("2026-03-30 10:00"), 2.0),
            ],
            columns=["point_id", "ts_utc", "value"],
        ),
    )
    return c


def _spec(check_id: str) -> CheckSpec:
    specs = {s.id: s for s in load_checks("platform/quality/checks")}
    s = specs[check_id]
    data = s.model_dump()
    for f in ("sql_checked", "sql_failed", "sql_checked_by_building"):
        if data.get(f):
            data[f] = data[f].replace("{window_end}", WINDOW_END).replace("{lake}", "nope")
    return CheckSpec(**data)


# check_id -> (expected_checked, expected_failed)
EXPECTATIONS = {
    "spaces_teaching_capacity": (2, 1),
    "spaces_gia_consistent": (2, 1),
    "assets_install_not_future": (2, 1),
    "wo_chronology": (2, 1),
    "wo_ppm_has_asset": (3, 1),
    "wo_no_future_raised": (7, 1),
    "wo_open_aged": (5, 1),
    "ma_id_known": (3, 1),
    "ma_no_future_ts": (4, 1),
    "ma_timeliness_per_meter": (3, 2),
    "tt_no_future_date": (3, 1),
    "tt_hours_sane": (3, 1),
    "insp_completed_sane": (3, 1),
    "sensors_id_known": (2, 1),
    "sensors_no_future_ts": (2, 0),
    "sensors_timeliness_per_sensor": (2, 1),
    "bms_no_future_ts": (3, 0),
    "bms_grain_dup_rate": (3, 1),
}


@pytest.mark.parametrize("check_id,expected", list(EXPECTATIONS.items()))
def test_sql_check_counts(con, check_id, expected):
    spec = _spec(check_id)
    res = sqlchecks.evaluate(con, spec)
    assert (res.rows_checked, res.rows_failed) == expected, check_id
    assert 0.0 <= res.pass_rate <= 1.0
    assert len(res.samples) <= 100


def test_by_building_pairs(con):
    res = sqlchecks.evaluate(con, _spec("spaces_gia_consistent"))
    assert res.by_building == {"B1": {"checked": 1, "failed": 0}, "B2": {"checked": 1, "failed": 1}}
    res = sqlchecks.evaluate(con, _spec("wo_open_aged"))
    assert res.by_building["B1"] == {"checked": 4, "failed": 1}
    assert res.by_building["B2"] == {"checked": 1, "failed": 0}


def test_status_thresholds():
    assert sqlchecks.status_of(1.0, 100.0) == "pass"
    assert sqlchecks.status_of(0.979, 98.0) == "fail"
    assert sqlchecks.status_of(0.98, 98.0) == "pass"


def test_bms_timeliness_scalar_cases(con):
    spec = _spec("bms_timeliness")
    res = sqlchecks.evaluate(con, spec)
    assert (res.rows_checked, res.rows_failed) == (1, 0)
    con.unregister("silver_bms")
    con.register(
        "silver_bms",
        pd.DataFrame(
            [("P1", _ts("2020-01-01"))],
            columns=["point_id", "ts_utc"],
        ).assign(value=1.0),
    )
    res = sqlchecks.evaluate(con, spec)
    assert (res.rows_checked, res.rows_failed) == (1, 1)
