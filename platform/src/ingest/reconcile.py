"""Reconciliation: raw rows = bronze rows; silver + quarantine = bronze (per source)."""

from __future__ import annotations

import pandas as pd


def reconcile_counts(raw: int, bronze: int, silver: int, quarantine: int, grain: str = "row") -> dict[str, object]:
    ok_raw = raw == bronze
    ok_sq = silver + quarantine == bronze
    return {
        "raw": raw,
        "bronze": bronze,
        "silver": silver,
        "quarantine": quarantine,
        "grain": grain,
        "raw_eq_bronze": ok_raw,
        "silver_plus_q_eq_bronze": ok_sq,
        "unexplained": bronze - silver - quarantine,
        "pass": bool(ok_raw and ok_sq),
    }


def raw_row_count(path: object, source: str = "") -> int:
    import pathlib

    p = pathlib.Path(str(path))
    if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        xls = pd.read_excel(p, sheet_name=None, header=None)
        if source == "space_register":
            # 2 merged title rows + 1 header row per sheet are not data
            return int(sum(max(0, len(d) - 3) for d in xls.values()))
        # 1 header row per sheet
        return int(sum(max(0, len(d) - 1) for d in xls.values()))
    if p.suffix.lower() == ".parquet":
        return int(len(pd.read_parquet(p)))
    # csv: count data rows (exclude header)
    with open(p, encoding="utf-8", errors="replace") as f:
        return max(0, sum(1 for _ in f) - 1)
