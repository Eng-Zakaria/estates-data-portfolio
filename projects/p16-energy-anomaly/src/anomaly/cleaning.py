"""Cleaning: gaps, zero runs, flat-lines, unit sanity, winsorising (fit-only)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def flag_flatline(s: pd.Series, window: int = 48) -> pd.Series:
    """True where the trailing `window` readings are all identical (and non-null)."""
    same = s.eq(s.shift(1))
    run = same.rolling(window - 1, min_periods=window - 1).apply(lambda w: bool(w.all()), raw=True)
    return pd.Series(np.nan_to_num(run.to_numpy(float), nan=0.0).astype(bool), index=s.index)


def cleaning_report(df: pd.DataFrame, value_col: str = "value") -> dict[str, float | int]:
    v = pd.to_numeric(df[value_col], errors="coerce")
    return {
        "n": int(len(df)),
        "n_null": int(v.isna().sum()),
        "n_negative": int((v < 0).sum()),
        "n_zero": int((v == 0).sum()),
        "flatline_windows": int(flag_flatline(v).sum()),
    }


def winsorise_fit(values: np.ndarray, lower_q: float = 0.01, upper_q: float = 0.99) -> np.ndarray:
    """Clip extremes for baseline FITTING only; detection always uses raw residuals.

    Returns the input unchanged when it holds no finite value (a meter whose
    training window is entirely missing): there is nothing to fit a bound from,
    and inventing one would fabricate a baseline.
    """
    v = np.asarray(values, dtype=float)
    finite = v[np.isfinite(v)]
    if len(finite) == 0:
        return v
    lo, hi = np.quantile(finite, [lower_q, upper_q])
    return np.clip(v, lo, hi)
