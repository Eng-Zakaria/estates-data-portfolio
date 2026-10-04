"""Silver: cafm_workorders → silver.work_orders (+ quarantine)."""

from __future__ import annotations

import pandas as pd

from .dates import parse_with_candidates
from .silver_common import clean_currency, dedupe, norm_status, quarantine


def transform_cafm(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    # mandatory
    miss = df["WO_Number"].isna() | df["AssetRef"].isna() | df["Raised"].isna()
    valid, q_null = quarantine(df, miss, "nulls_in_mandatory")
    # dates with candidate logging
    raised, raised_fmt = parse_with_candidates(valid["Raised"].astype(str))
    completed, _ = parse_with_candidates(valid["Completed"].astype(str))
    valid["raised_ts"] = pd.to_datetime(raised, utc=True, errors="coerce")
    valid["completed_ts"] = pd.to_datetime(completed, utc=True, errors="coerce")
    valid["_raised_fmt"] = raised_fmt
    valid, q_date = quarantine(valid, valid["raised_ts"].isna(), "future_dates:unparseable_raised")
    # future dates
    now = pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=1)
    future = valid["raised_ts"] > now
    valid, q_future = quarantine(valid, future, "future_dates:raised_in_future")
    # completed before/at raised (strictly, equal is impossible with labour) — catches planted defect
    bad_order = valid["completed_ts"].notna() & (valid["completed_ts"] <= valid["raised_ts"])
    valid, q_order = quarantine(valid, bad_order, "completed_before_raised")
    # cost / hours
    valid["cost_gbp"] = clean_currency(valid["Cost"])
    valid["labour_hours"] = pd.to_numeric(valid["labour_hours"], errors="coerce")
    # only quarantine negative costs, not missing
    neg = (valid["cost_gbp"] < 0).fillna(False)
    valid, q_cost = quarantine(valid, neg, "out_of_range:negative_cost")
    # status / enums
    valid["status"] = norm_status(valid["Status"])
    bad_enum = ~valid["wo_type"].isin(["PPM", "Reactive", "Statutory", "Project"]) | ~valid["priority"].isin(
        ["P1", "P2", "P3", "P4"]
    )
    valid, q_enum = quarantine(valid, bad_enum.fillna(True), "validity:bad_wo_type_or_priority")
    # dedupe
    valid, q_dup = dedupe(valid, ["WO_Number"])
    silver = valid[
        [
            "WO_Number",
            "AssetRef",
            "space_id",
            "building_id",
            "wo_type",
            "priority",
            "raised_ts",
            "completed_ts",
            "status",
            "trade",
            "contractor",
            "labour_hours",
            "cost_gbp",
        ]
    ].copy()
    parts = [q_null, q_date, q_future, q_order, q_cost, q_enum, q_dup]
    quarantine_all = pd.concat(parts, ignore_index=True) if any(len(q) for q in parts) else valid.iloc[0:0].copy()
    return silver.reset_index(drop=True), quarantine_all.reset_index(drop=True)
