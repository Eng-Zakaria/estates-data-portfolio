"""Shared silver helpers: quarantine split, dedupe, cleaners."""

from __future__ import annotations

import pandas as pd


def quarantine(df: pd.DataFrame, mask: pd.Series | object, reason: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split valid/quarantine. Quarantine gets _reject_reason; valid drops the mask."""
    if isinstance(mask, pd.Series):
        m = mask.fillna(False).to_numpy(dtype=bool)
    else:
        import numpy as np

        m = np.asarray(mask, dtype=bool)
    q = df[m].copy()
    q["_reject_reason"] = reason
    return df[~m].copy(), q


def dedupe(df: pd.DataFrame, keys: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    dup = df.duplicated(subset=keys, keep="first")
    valid, q = quarantine(df, dup, f"duplicate:{'+'.join(keys)}")
    return valid, q


def clean_currency(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace("£", "", regex=False).str.replace(",", "", regex=False), errors="coerce"
    )


def clean_area(s: pd.Series) -> pd.Series:
    num = s.astype(str).str.extract(r"([-+]?\d*\.?\d+)")[0]
    return pd.to_numeric(num, errors="coerce")


def norm_status(s: pd.Series) -> pd.Series:
    m = {"COMP": "Complete", "Closed": "Complete", "OPEN": "Open", "Outstanding": "Open"}
    return s.astype(str).str.strip().replace(m)
