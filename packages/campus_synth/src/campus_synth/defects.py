"""Catalogued defect injection. Every defect is logged for ground_truth.yaml."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DEFECT_TYPES = [
    "duplicate_rows",
    "nulls_in_mandatory",
    "out_of_range",
    "orphan_fk",
    "misspelt_category",
    "future_dates",
    "completed_before_raised",
    "area_totals_exceed_gia",
    "negative_or_spiked_meter",
    "flat_lined_meter",
    "gaps",
    "meter_rollover",
    "dst_duplicates",
    "unit_mixup",
    "stale_file",
]


@dataclass
class DefectLog:
    table: str
    row_key: str
    type: str


def _n(rng: np.random.Generator, n_rows: int, rate: float) -> int:
    return int(round(n_rows * rate))


def inject_defects(
    df: pd.DataFrame,
    table: str,
    rng: np.random.Generator,
    defect_rate: float,
    key_col: str | None = None,
    numeric_cols: list[str] | None = None,
    date_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Inject a small catalogue of defects scaled by defect_rate. Returns (frame, log).

    Vectorised (no per-row iloc loops) so 700k+ row frames stay fast.
    Every injected row is logged so injected counts equal log counts.
    """
    if df.empty or defect_rate <= 0:
        return df.copy(), []
    out = df.copy()
    logs: list[dict[str, str]] = []
    n = len(out)
    key = key_col if key_col in out.columns else out.columns[0]
    keys = out[key].astype(str).to_numpy()

    # 1. duplicate rows (~20% of defect budget)
    n_dup = max(1, _n(rng, n, defect_rate * 0.2)) if n > 5 else 0
    if n_dup:
        picks = rng.choice(n, size=min(n_dup, n), replace=False)
        dups = out.iloc[picks].copy()
        out = pd.concat([out, dups], ignore_index=True)
        keys = out[key].astype(str).to_numpy()
        for p in picks:
            logs.append({"table": table, "row_key": str(keys[int(p)]), "type": "duplicate_rows"})

    # 2. nulls in mandatory fields (vectorised single loc)
    n_null = _n(rng, n, defect_rate * 0.2)
    if n_null and len(out.columns) > 1:
        col = out.columns[1]
        picks = rng.choice(len(out), size=min(n_null, len(out)), replace=False)
        out.loc[out.index[picks], col] = None
        keys = out[key].astype(str).to_numpy()
        for p in picks:
            logs.append({"table": table, "row_key": str(keys[int(p)]), "type": "nulls_in_mandatory"})

    # 3. out-of-range (negative numerics, vectorised)
    n_oor = _n(rng, n, defect_rate * 0.15)
    num_cols = numeric_cols or [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
    if n_oor and num_cols:
        col = num_cols[0]
        picks = rng.choice(len(out), size=min(n_oor, len(out)), replace=False)
        vals = pd.to_numeric(out.loc[out.index[picks], col], errors="coerce").fillna(1.0).abs()
        out.loc[out.index[picks], col] = -vals.to_numpy()
        keys = out[key].astype(str).to_numpy()
        for p in picks:
            logs.append({"table": table, "row_key": str(keys[int(p)]), "type": "out_of_range"})

    # 4. misspelt categories (vectorised string op)
    str_cols = [c for c in out.columns if out[c].dtype == object]
    n_mis = _n(rng, n, defect_rate * 0.15)
    if n_mis and str_cols:
        col = str_cols[0]
        picks = rng.choice(len(out), size=min(n_mis, len(out)), replace=False)
        idx = out.index[picks]
        s = out.loc[idx, col].astype(str)
        out.loc[idx, col] = s.str.slice(0, -2) + "xx"
        keys = out[key].astype(str).to_numpy()
        for p in picks:
            logs.append({"table": table, "row_key": str(keys[int(p)]), "type": "misspelt_category"})

    # 5. future dates (vectorised)
    n_fut = _n(rng, n, defect_rate * 0.1)
    dcols = date_cols or [c for c in out.columns if "date" in c.lower() or "_ts" in c.lower() or c == "ts_utc"]
    if n_fut and dcols:
        col = dcols[0]
        picks = rng.choice(len(out), size=min(n_fut, len(out)), replace=False)
        out.loc[out.index[picks], col] = "2099-01-01"
        keys = out[key].astype(str).to_numpy()
        for p in picks:
            logs.append({"table": table, "row_key": str(keys[int(p)]), "type": "future_dates"})

    # 6. orphan FKs (append ≤3 rows with bad keys)
    n_orp = _n(rng, n, defect_rate * 0.1)
    if n_orp and any(c in out.columns for c in ("building_id", "space_id", "asset_id")):
        fk = next(c for c in ("building_id", "space_id", "asset_id") if c in out.columns)
        for _ in range(max(1, min(n_orp, 3))):
            bad = out.iloc[0].copy()
            bad[fk] = "B999-ORPHAN"
            out = pd.concat([out, bad.to_frame().T], ignore_index=True)
            logs.append({"table": table, "row_key": "B999-ORPHAN", "type": "orphan_fk"})

    return out.reset_index(drop=True), logs
