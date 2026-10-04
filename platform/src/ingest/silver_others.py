"""Silver: inspections, timetable, sensors, BMS."""

from __future__ import annotations

import pandas as pd

from .dates import parse_with_candidates
from .silver_common import dedupe, quarantine

RESULT_MAP = {
    "pass - ok": "Pass",
    "Satisfactory": "Pass",
    "pass": "Pass",
    "FAIL - remedial needed": "Fail",
    "unsat": "Fail",
    "fail": "Fail",
    "Advisory - monitor": "Advisory",
}


def transform_inspections(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    miss = df["inspection_id"].isna() | df["building_id"].isna() | df["due_messy"].isna()
    valid, q_null = quarantine(df, miss, "nulls_in_mandatory")
    due, _ = parse_with_candidates(valid["due_messy"].astype(str))
    comp, _ = parse_with_candidates(valid["completed_messy"].astype(str))
    valid["due_date"] = pd.to_datetime(due).dt.date
    valid["completed_date"] = pd.to_datetime(comp).dt.date
    valid, q_due = quarantine(valid, valid["due_date"].isna(), "future_dates:unparseable_due")
    valid["result"] = valid["result_text"].astype(str).str.strip().replace(RESULT_MAP)
    valid.loc[valid["result_text"].isna(), "result"] = None
    bad = ~valid["result"].isin(["Pass", "Fail", "Advisory", None, "nan"]) & valid["result"].notna()
    valid, q_res = quarantine(valid, bad.fillna(False), "validity:bad_result")
    valid, q_dup = dedupe(valid, ["inspection_id"])
    silver = valid[
        ["inspection_id", "building_id", "inspection_type_id", "due_date", "completed_date", "result"]
    ].copy()
    parts = [q_null, q_due, q_res, q_dup]
    qall = pd.concat(parts, ignore_index=True) if any(len(q) for q in parts) else valid.iloc[0:0].copy()
    return silver.reset_index(drop=True), qall.reset_index(drop=True)


def transform_timetable(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    miss = df["event_id"].isna() | df["space_id"].isna() | df["date"].isna() | df["time"].isna()
    valid, q_null = quarantine(df, miss, "nulls_in_mandatory")
    # time HH:MM-HH:MM
    tm = valid["time"].astype(str).str.extract(r"(?P<s>\d{2}:\d{2})-(?P<e>\d{2}:\d{2})")
    valid["t_start"] = tm["s"]
    valid["t_end"] = tm["e"]
    valid, q_time = quarantine(valid, valid["t_start"].isna(), "validity:bad_time_range")
    valid["group_size"] = pd.to_numeric(valid["group_size"], errors="coerce")
    valid, q_grp = quarantine(valid, valid["group_size"].isna() | (valid["group_size"] < 0), "out_of_range:group_size")
    valid, q_dup = dedupe(valid, ["event_id"])
    silver = valid[["event_id", "space_id", "date", "t_start", "t_end", "module_code", "group_size"]].copy()
    parts = [q_null, q_time, q_grp, q_dup]
    qall = pd.concat(parts, ignore_index=True) if any(len(q) for q in parts) else valid.iloc[0:0].copy()
    return silver.reset_index(drop=True), qall.reset_index(drop=True)


def transform_sensors(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    miss = df["sensor_id"].isna() | df["ts_utc"].isna() | df["value"].isna()
    valid, q_null = quarantine(df, miss, "nulls_in_mandatory")
    valid["ts_utc"] = pd.to_datetime(valid["ts_utc"], utc=True, errors="coerce")
    valid, q_time = quarantine(valid, valid["ts_utc"].isna(), "future_dates:unparseable_ts")
    future = valid["ts_utc"] > (pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=1))
    valid, q_future = quarantine(valid, future.fillna(False), "future_dates:ts_in_future")
    valid["value"] = pd.to_numeric(valid["value"], errors="coerce")
    valid, q_num = quarantine(valid, valid["value"].isna(), "validity:non_numeric_value")
    valid, q_dup = dedupe(valid, ["sensor_id", "ts_utc"])
    silver = valid[["sensor_id", "ts_utc", "value"]].copy()
    parts = [q_null, q_time, q_future, q_num, q_dup]
    qall = pd.concat(parts, ignore_index=True) if any(len(q) for q in parts) else valid.iloc[0:0].copy()
    return silver.reset_index(drop=True), qall.reset_index(drop=True)


def transform_bms(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    # timestamp col is first col (named timestamp after export)
    ts_col = "timestamp" if "timestamp" in df.columns else df.columns[0]
    valid = df.copy()
    valid["ts_utc"] = pd.to_datetime(valid[ts_col], utc=True, errors="coerce")
    valid, q_time = quarantine(valid, valid["ts_utc"].isna(), "future_dates:unparseable_ts")
    audit = {"_ingest_id", "_source_system", "_source_file", "_loaded_at", "_row_number", "_row_hash", "_sheet"}
    point_cols = [c for c in df.columns if c != ts_col and c not in audit and not c.startswith("_")]
    # N/A strings → long quarantine entries (one row per bad cell, all of them)
    bad_cells = []
    for c in point_cols:
        series = pd.to_numeric(valid[c], errors="coerce")
        bad = series.isna() & valid[c].notna()
        for idx in valid[bad].index:
            bad_cells.append(
                {"point": c, "ts": str(valid.loc[idx, ts_col]), "_reject_reason": "nulls_in_mandatory:N/A"}
            )
    q_na = pd.DataFrame(bad_cells)
    # long valid readings (numeric only)
    frames = []
    for c in point_cols:
        series = pd.to_numeric(valid[c], errors="coerce")
        ok = series.notna()
        frames.append(
            pd.DataFrame({"point_id": c, "ts_utc": valid.loc[ok, "ts_utc"].to_numpy(), "value": series[ok].to_numpy()})
        )
    silver = pd.concat(frames, ignore_index=True) if frames else valid.iloc[0:0].copy()
    parts = [q_time, q_na] if len(q_na) else [q_time]
    qall = pd.concat(parts, ignore_index=True) if any(len(q) for q in parts) else valid.iloc[0:0].copy()
    return silver.reset_index(drop=True), qall.reset_index(drop=True)
