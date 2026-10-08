"""Tests for the loaders: campus synthetic truth tree and BDG2 subset extraction.

BDG2 fixtures are hand-built CSVs mirroring the real archive layout
(verified in data_bdg2 module docstring); no network or zip is touched here.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from anomaly.data_bdg2 import load_bdg2_subset
from anomaly.data_campus import load_campus


def _write_campus_truth(root: Path) -> None:
    ts = pd.date_range("2026-01-01", periods=48, freq="30min", tz="UTC")
    readings = pd.DataFrame(
        {
            "meter_id": ["M-B001-E01"] * 48 + ["M-B001-G01"] * 48,
            "ts_utc": list(ts) * 2,
            "value": np.concatenate([np.linspace(1, 2, 48), np.linspace(3, 4, 48)]),
        }
    )
    pd.DataFrame(
        {
            "meter_id": ["M-B001-E01", "M-B001-G01", "M-B001-W01"],
            "building_id": ["B001", "B001", "B001"],
            "utility": ["electricity", "gas", "water"],
        }
    ).to_parquet(root / "meters.parquet", index=False)
    readings.to_parquet(root / "meter_readings_hh.parquet", index=False)
    pd.DataFrame({"ts_utc": list(ts), "temp_c": 10.0}).to_parquet(root / "weather.parquet", index=False)


def test_load_campus_merges_and_filters_utility(tmp_path: Path) -> None:
    _write_campus_truth(tmp_path)
    df, weather = load_campus(truth_dir=tmp_path)
    # water meter dropped: electricity + gas only
    assert set(df["meter_id"]) == {"M-B001-E01", "M-B001-G01"}
    assert df["building_id"].unique().tolist() == ["B001"]
    assert str(df["ts_utc"].dtype) == "datetime64[ns, UTC]"
    assert str(weather["ts_utc"].dtype) == "datetime64[ns, UTC]"
    assert len(df) == 96


def test_load_campus_filters_meters_and_sorts(tmp_path: Path) -> None:
    _write_campus_truth(tmp_path)
    df, _ = load_campus(meters=["M-B001-G01"], truth_dir=tmp_path)
    assert df["meter_id"].unique().tolist() == ["M-B001-G01"]
    assert df["ts_utc"].is_monotonic_increasing


def _write_bdg2_subset(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    # US/Eastern stamps covering both 2017 DST transitions:
    # 2017-03-12 02:00 does not exist (spring forward, shifted to 03:00) and
    # 2017-11-05 01:00 occurs twice (autumn, ambiguous -> NaT -> dropped);
    # 02:00 EST on 2017-11-05 is unambiguous and must survive.
    stamps = ["2017-03-12 01:00", "2017-03-12 02:00", "2017-11-05 01:00", "2017-11-05 02:00"]
    pd.DataFrame(
        {
            "timestamp": stamps,
            "b_edu_1": [1.0, 2.0, 3.0, 4.0],
            "b_edu_2": [5.0, 6.0, 7.0, 8.0],
            "b_retail_1": [9.0, 9.0, 9.0, 9.0],
        }
    ).to_csv(root / "electricity_cleaned.csv", index=False)
    pd.DataFrame(
        {
            "building_id": ["b_edu_1", "b_edu_2", "b_retail_1"],
            "site_id": ["Rat", "Rat", "Rat"],
            "primaryspaceusage": ["Education", "Education", "Retail"],
            "electricity": [1.0, 1.0, 1.0],
            "timezone": ["US/Eastern", "US/Eastern", "US/Eastern"],
        }
    ).to_csv(root / "metadata.csv", index=False)
    pd.DataFrame(
        {
            "site_id": ["Rat"] * len(stamps),
            "timestamp": stamps,
            "airTemperature": [5.0, 6.0, 7.0, 8.0],
        }
    ).to_csv(root / "weather.csv", index=False)
    (root / "buildings.csv").write_text("building_id\nb_edu_1\nb_edu_2\n", encoding="utf-8")


def test_load_bdg2_subset_localises_to_utc_and_drops_ambiguous(tmp_path: Path) -> None:
    _write_bdg2_subset(tmp_path / "subset")
    readings, weather = load_bdg2_subset(tmp_path / "subset")
    assert set(readings["building"]) == {"b_edu_1", "b_edu_2"}
    assert set(readings.columns) >= {"building", "site", "ts_utc", "value"}
    assert str(readings["ts_utc"].dtype) == "datetime64[ns, UTC]"
    b1 = readings[readings.building == "b_edu_1"].sort_values("ts_utc")
    assert b1["ts_utc"].is_monotonic_increasing
    assert b1["ts_utc"].is_unique
    # 01:00 EST -> 06:00 UTC; nonexistent 02:00 shifted to 03:00 EDT -> 07:00 UTC;
    # ambiguous autumn 01:00 dropped (never fabricated); 02:00 EST -> 07:00 UTC.
    assert b1["value"].tolist() == [1.0, 2.0, 4.0]
    assert pd.Timestamp("2017-03-12 06:00", tz="UTC") in set(b1["ts_utc"])
    assert pd.Timestamp("2017-03-12 07:00", tz="UTC") in set(b1["ts_utc"])
    assert pd.Timestamp("2017-11-05 07:00", tz="UTC") in set(b1["ts_utc"])
    assert set(weather["site"]) == {"Rat"}
    # same rule applies to weather: the ambiguous hour is dropped
    assert weather["temp_c"].tolist() == [5.0, 6.0, 8.0]


def test_load_bdg2_subset_missing_cache_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_bdg2_subset(tmp_path / "nope")
