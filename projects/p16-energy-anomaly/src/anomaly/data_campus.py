"""Campus synthetic HH loader (default profile for planted B007/B019/M-B015)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

TRUTH = Path("data/truth")
DEFAULT_CACHE = Path("data/p16_default")


def load_campus(meters: list[str] | None = None, truth_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (readings HH with meter+building+utility, weather). Raises if data missing.

    `truth_dir` points at an alternate truth tree (e.g. the default-profile
    cache in data/p16_default for planted B019/M-B015); defaults to data/truth.
    """
    truth = truth_dir or TRUTH
    readings = pd.read_parquet(truth / "meter_readings_hh.parquet")
    meta = pd.read_parquet(truth / "meters.parquet")[["meter_id", "building_id", "utility"]]
    weather = pd.read_parquet(truth / "weather.parquet")
    df = readings.merge(meta, on="meter_id", how="left")
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    if meters is not None:
        df = df[df.meter_id.isin(meters)].copy()
    df = df[df.utility.isin(["electricity", "gas"])].copy()
    weather["ts_utc"] = pd.to_datetime(weather["ts_utc"], utc=True)
    return df.sort_values(["meter_id", "ts_utc"]).reset_index(drop=True), weather


def planted_meters() -> dict[str, str]:
    return {
        "overnight": "M-B007-E01",
        "summer_gas": "M-B019-G01",
        "flatline": "M-B015-E01",
    }
