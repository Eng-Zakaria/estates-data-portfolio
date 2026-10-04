"""Silver: meter HH (supplier A long + supplier B wide) → silver.meter_hh (UTC) + quarantine + gaps report."""

from __future__ import annotations

import pandas as pd

from .silver_common import dedupe, quarantine

LONDON = "Europe/London"


def _local_to_utc(s: pd.Series, fmt: str = "%d/%m/%Y %H:%M") -> tuple[pd.Series, pd.Series]:
    """Parse naive local strings → London → UTC. Ambiguous/nonexistent → NaT (quarantined)."""
    naive = pd.to_datetime(s.astype(str), format=fmt, errors="coerce")
    # localise; ambiguous/nonexistent become NaT
    try:
        loc = naive.dt.tz_localize(LONDON, ambiguous="NaT", nonexistent="NaT")
    except Exception:
        loc = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns, Europe/London]")
    utc = loc.dt.tz_convert("UTC")
    ok = utc.notna()
    return utc, ok


def cumulative_to_interval(vals: pd.Series, rollover: float | None = None) -> tuple[pd.Series, bool, float | None]:
    """Detect cumulative registers (monotonic, large) and diff them with rollover."""
    v = pd.to_numeric(vals, errors="coerce")
    if v.isna().all() or len(v) < 3:
        return v, False, None
    diffs = v.diff().dropna()
    nonneg_rate = float((diffs >= 0).mean())
    has_rollover_drop = bool((diffs < -1000).any())
    median_diff = float(diffs.median())
    if v.max() > 1000 and (nonneg_rate > 0.95 or (nonneg_rate > 0.6 and has_rollover_drop)) and median_diff >= 0:
        ro = rollover or float(v.max() * 1.2)
        d = v.diff()
        d[d < 0] += ro  # rollover correction
        return d.fillna(0), True, ro
    return v, False, None


def transform_meter_A(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    miss = df["meter_id"].isna() | df["local_time"].isna() | df["kwh"].isna()
    valid, q_null = quarantine(df, miss, "nulls_in_mandatory")
    utc, ok = _local_to_utc(valid["local_time"])
    valid["ts_utc"] = utc
    valid, q_time = quarantine(valid, ~ok.to_numpy(), "dst:ambiguous_or_nonexistent_local")
    valid["value"] = pd.to_numeric(valid["kwh"], errors="coerce")
    valid, q_num = quarantine(valid, valid["value"].isna(), "validity:non_numeric_kwh")
    neg = (valid["value"] < 0).fillna(False)
    valid, q_neg = quarantine(valid, neg, "negative_or_spiked_meter:negative_kwh")
    # cumulative detection per meter
    cum_notes = []
    for mid, grp in valid.groupby("meter_id"):
        vals, was_cum, ro = cumulative_to_interval(grp["value"])
        if was_cum:
            valid.loc[grp.index, "value"] = vals.to_numpy()
            cum_notes.append({"meter_id": mid, "cumulative": True, "rollover": ro})
    # dedupe by meter+ts
    valid, q_dup = dedupe(valid, ["meter_id", "ts_utc"])
    silver = valid[["meter_id", "ts_utc", "value"]].copy()
    silver["unit"] = "kWh"
    silver["quality_flag"] = "ok"
    parts = [q_null, q_time, q_num, q_neg, q_dup]
    quarantine_all = pd.concat(parts, ignore_index=True) if any(len(q) for q in parts) else valid.iloc[0:0].copy()
    gaps = _gaps_report(silver)
    _ = cum_notes
    return silver.reset_index(drop=True), quarantine_all.reset_index(drop=True), gaps


def transform_meter_B(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    hh_cols = [c for c in df.columns if c.startswith("HH")]
    if not hh_cols:
        q = df.copy()
        q["_reject_reason"] = "validity:no_HH_columns"
        return df.iloc[0:0].copy(), q, df.iloc[0:0].copy()
    long = df.melt(id_vars=["meter_id", "local_date"], value_vars=hh_cols, var_name="slot", value_name="value")
    long["slot_n"] = long["slot"].str.extract(r"HH(\d+)").astype(int)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long, q_empty = quarantine(long, long["value"].isna(), "nulls_in_mandatory:empty_HH_cell")
    # reconstruct local timestamps: local_date + (slot-1)*30min
    base = pd.to_datetime(long["local_date"], errors="coerce")
    long["local_naive"] = base + pd.to_timedelta((long["slot_n"] - 1) * 30, unit="m")
    try:
        loc = long["local_naive"].dt.tz_localize(LONDON, ambiguous="NaT", nonexistent="NaT")
    except Exception:
        loc = pd.Series(pd.NaT, index=long.index, dtype="datetime64[ns, Europe/London]")
    long["ts_utc"] = loc.dt.tz_convert("UTC").to_numpy()
    valid, q_time = quarantine(long, long["ts_utc"].isna(), "dst:ambiguous_or_nonexistent_local")
    neg = (valid["value"] < 0).fillna(False)
    valid, q_neg = quarantine(valid, neg, "negative_or_spiked_meter:negative_kwh")
    valid, q_dup = dedupe(valid, ["meter_id", "ts_utc"])
    silver = valid[["meter_id", "ts_utc", "value"]].copy()
    silver["unit"] = "kWh"
    silver["quality_flag"] = "ok"
    parts = [q_empty, q_time, q_neg, q_dup]
    quarantine_all = pd.concat(parts, ignore_index=True) if any(len(q) for q in parts) else valid.iloc[0:0].copy()
    gaps = _gaps_report(silver)
    return silver.reset_index(drop=True), quarantine_all.reset_index(drop=True), gaps


def _gaps_report(silver: pd.DataFrame) -> pd.DataFrame:
    """Per meter-day: expected (48, 46/50 DST) vs actual. Flag only, never fabricate."""
    if silver.empty:
        return pd.DataFrame(columns=["meter_id", "local_date", "expected", "actual", "missing"])
    s = silver.copy()
    s["local_date"] = pd.to_datetime(s["ts_utc"], utc=True).dt.tz_convert(LONDON).dt.date.astype(str)
    rows = []
    # Spring 46 / autumn 50; default 48. Covers small + full windows.
    short = {
        "2026-03-29": 46,
        "2024-03-31": 46,
        "2025-03-30": 46,
        "2024-10-27": 50,
        "2025-10-26": 50,
        "2026-10-25": 50,
    }
    for (mid, ld), grp in s.groupby(["meter_id", "local_date"]):
        exp = short.get(str(ld), 48)
        act = int(grp["ts_utc"].nunique())
        if act != exp:
            rows.append({"meter_id": mid, "local_date": str(ld), "expected": exp, "actual": act, "missing": exp - act})
    return pd.DataFrame(rows, columns=["meter_id", "local_date", "expected", "actual", "missing"])
