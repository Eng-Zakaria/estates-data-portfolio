"""The nightly export to the P01 `bms_trends` contract.

The lakehouse rejects a file that does not match `platform/contracts/bms_trends.yml`,
so the shape is asserted here rather than discovered during a P01 ingest run.
"""

from __future__ import annotations

import re
from datetime import date

import pandas as pd
import pytest
from conftest import START

from export_bms_trends import NA, TS_FORMAT, to_wide, write_bms_trends
from export_sql import build_sql

REGISTRY = {
    "B001.ahu_01.supply_temp": {"unit": "C"},
    "B001.ahu_01.fan_speed": {"unit": "%"},
    "B001.room_01.co2": {"unit": "ppm"},
}


def sample_readings() -> pd.DataFrame:
    base = pd.Timestamp(START)
    return pd.DataFrame(
        {
            "ts": [base, base, base, base + pd.Timedelta(minutes=5), base + pd.Timedelta(minutes=5)],
            "point_id": [
                "B001.ahu_01.supply_temp",
                "B001.ahu_01.fan_speed",
                "B001.room_01.co2",
                "B001.ahu_01.supply_temp",
                "B001.ahu_01.fan_speed",
            ],
            "value": [12.0, 15.0, 430.0, 12.5, 75.0],
            "unit": ["C", "%", "ppm", "C", "%"],
            "quality": ["good"] * 5,
        }
    )


# ---------------------------------------------------------------- shape
def test_wide_shape_is_timestamp_plus_one_column_per_point():
    wide = to_wide(sample_readings(), REGISTRY)
    assert list(wide.columns) == [
        "timestamp",
        "B001.ahu_01.fan_speed [%]",
        "B001.ahu_01.supply_temp [C]",
        "B001.room_01.co2 [ppm]",
    ]
    assert len(wide) == 2


def test_column_names_carry_the_unit_so_the_header_is_self_describing():
    wide = to_wide(sample_readings(), REGISTRY)
    for column in wide.columns[1:]:
        assert column.endswith("]") and " [" in column


def test_timestamps_are_iso_with_an_offset():
    """P01's date_candidates only match the offset form; a naive timestamp
    would land in the quarantine table instead of silver."""
    wide = to_wide(sample_readings(), REGISTRY)
    for stamp in wide["timestamp"]:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4}", stamp), stamp
        assert pd.Timestamp(stamp).tzinfo is not None


def test_timestamps_are_rendered_in_site_local_time():
    """The site clock is Europe/London, so 23:00 UTC on 7 Oct is 00:00 on 8 Oct
    BST; the export must carry the local date an operator would recognise."""
    wide = to_wide(sample_readings(), REGISTRY)
    assert wide["timestamp"].iloc[0].startswith("2026-10-08T00:00:00+0100")


def test_missing_cells_become_the_n_a_string():
    """P01 quarantines N/A cells as nulls_in_mandatory, which is the intended
    signal that a point stopped reporting."""
    wide = to_wide(sample_readings(), REGISTRY)
    assert wide["B001.room_01.co2 [ppm]"].tolist() == [430.0, NA]


def test_values_are_rounded_not_truncated():
    wide = to_wide(sample_readings(), REGISTRY)
    assert wide["B001.ahu_01.supply_temp [C]"].tolist() == [12.0, 12.5]


def test_last_delivery_wins_for_a_repeated_timestamp():
    """Re-delivery is normal (at-least-once MQTT); the export must not
    duplicate a timestamp column row."""
    readings = sample_readings()
    dup = readings.iloc[[0]].copy()
    dup["value"] = 99.0
    wide = to_wide(pd.concat([readings, dup], ignore_index=True), REGISTRY)
    assert len(wide) == 2
    assert wide["B001.ahu_01.supply_temp [C]"].iloc[0] == 99.0


def test_units_fall_back_to_the_registry_when_the_reading_has_none():
    readings = sample_readings()
    readings["unit"] = None
    wide = to_wide(readings, REGISTRY)
    assert "B001.room_01.co2 [ppm]" in wide.columns


def test_non_numeric_readings_are_dropped():
    readings = sample_readings()
    readings["value"] = readings["value"].astype(object)
    readings.loc[0, "value"] = "not_a_number"
    wide = to_wide(readings, REGISTRY)
    # the bad cell was dropped, so its (ts, point) pair is unobserved -> "N/A"
    assert wide["B001.ahu_01.supply_temp [C]"].iloc[0] == "N/A"


def test_empty_readings_give_an_empty_frame_not_an_error():
    empty = pd.DataFrame(columns=["ts", "point_id", "value", "unit"])
    assert to_wide(empty, REGISTRY).empty


# ---------------------------------------------------------------- file
def test_written_file_matches_the_p01_filename_pattern(tmp_path):
    path = write_bms_trends(sample_readings(), tmp_path, registry=REGISTRY)
    assert re.fullmatch(r"bms_trends_\d{8}\.csv", path.name)


def test_written_file_has_a_timestamp_column_first(tmp_path):
    path = write_bms_trends(sample_readings(), tmp_path, registry=REGISTRY)
    frame = pd.read_csv(path)
    assert frame.columns[0] == "timestamp"


def test_written_file_date_can_be_stamped_explicitly(tmp_path):
    """The lakehouse expects the filename date to match the data's day, so the
    caller can pass it rather than infer it."""
    path = write_bms_trends(sample_readings(), tmp_path, date_stamp=date(2026, 10, 8), registry=REGISTRY)
    assert path.name == "bms_trends_20261008.csv"


def test_written_file_round_trips(tmp_path):
    """The N/A cells survive the file round trip: pandas parses them back as
    NaN, so the check reads the raw text rather than trusting a re-read."""
    path = write_bms_trends(sample_readings(), tmp_path, registry=REGISTRY)
    frame = pd.read_csv(path)
    assert frame["B001.room_01.co2 [ppm]"].iloc[0] == 430.0
    assert frame["B001.room_01.co2 [ppm]"].isna().iloc[1]
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    # line 1 is the 00:00 row (all three points present); line 2 is 00:05,
    # where the co2 point is missing -> its cell is the N/A marker
    second = lines[2].split(",")
    # columns are ordered fan_speed, supply_temp, co2, so the gap is the last cell
    assert header[-1] == "B001.room_01.co2 [ppm]"
    assert second[-1] == NA


def test_writing_nothing_is_an_error_rather_than_an_empty_file(tmp_path):
    empty = pd.DataFrame(columns=["ts", "point_id", "value", "unit"])
    with pytest.raises(ValueError):
        write_bms_trends(empty, tmp_path, registry=REGISTRY)


def test_out_of_range_round_to_argument():
    wide = to_wide(sample_readings(), REGISTRY, round_to=1)
    assert wide["B001.ahu_01.supply_temp [C]"].iloc[0] == 12.0


def test_timestamp_format_constant_is_what_the_contract_needs():
    assert TS_FORMAT == "%Y-%m-%dT%H:%M:%S%z"


# ---------------------------------------------------------------- sql
def test_generated_sql_covers_every_registry_point(registry):
    sql = build_sql()
    for point_id, row in registry.items():
        assert f"r.point_id = '{point_id}'" in sql
        assert f'"{point_id} [{row["unit"]}]"' in sql


def test_generated_sql_uses_the_hourly_aggregate_and_n_a_fallback():
    sql = build_sql(points=["B001.ahu_01.supply_temp"])
    assert "bms.readings_hourly" in sql
    assert "'N/A'" in sql
    assert "readings_hourly r" in sql


def test_generated_sql_formats_timestamps_with_an_offset():
    sql = build_sql(points=["B001.ahu_01.supply_temp"])
    assert "'Europe/London'" in sql
    assert 'HH24:MI:SSOF' in sql


def test_generated_sql_covers_the_last_24_hours_on_the_hour():
    sql = build_sql(points=["B001.ahu_01.supply_temp"])
    assert "INTERVAL '24 hours'" in sql
    assert "date_trunc('hour'" in sql


def test_generated_sql_writes_a_csv_with_a_header():
    sql = build_sql(points=["B001.ahu_01.supply_temp"])
    assert "\\copy (" in sql
    assert "FORMAT csv, HEADER true" in sql


def test_generated_sql_rejects_unknown_points():
    with pytest.raises(KeyError):
        build_sql(points=["not_a_point"])


def test_committed_sql_matches_the_registry(project, registry):
    """sql/export_bms_trends.sql is generated but committed; a stale copy would
    silently drop every point added since."""
    committed = (project / "sql" / "export_bms_trends.sql").read_text(encoding="utf-8")
    assert committed == build_sql(sorted(registry))