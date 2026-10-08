"""Baselines: (a) weekday/hour median profile, (b) temp + hour-of-week + holiday
regression, (c) gradient boosting. Rolling-origin CV with CVRMSE/NMBE."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge


def add_time_features(df: pd.DataFrame, ts_col: str = "ts_utc", temp_col: str | None = None) -> pd.DataFrame:
    d = df.copy()
    ts = pd.to_datetime(d[ts_col], utc=True)
    d["hour"] = ts.dt.hour + ts.dt.minute / 60.0
    d["dow"] = ts.dt.dayofweek
    d["hour_of_week"] = d["dow"] * 24 + ts.dt.hour
    d["is_weekend"] = (d["dow"] >= 5).astype(int)
    if temp_col and temp_col in d.columns:
        d["hdd"] = np.maximum(0.0, 15.5 - d[temp_col])
    return d


def baseline_median_profile(train: pd.DataFrame, value_col: str = "value") -> pd.Series:
    """Median by (dow, hour). Returns a lookup Series indexed by (dow, hour)."""
    t = add_time_features(train)
    return t.groupby(["dow", t["hour"].astype(int)])[value_col].median()


def apply_median_profile(df: pd.DataFrame, profile: pd.Series, value_col: str = "value") -> np.ndarray:
    t = add_time_features(df)
    key = list(zip(t["dow"].to_numpy(), t["hour"].astype(int).to_numpy()))
    return np.array([profile.get(k, np.nan) for k in key], dtype=float)


def design_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Design matrix for the Ridge/GBM baselines.

    Weather gaps are possible (BDG2 site weather is not gap-free), and both
    `Ridge` and this project contract reject NaN features. Missing heating
    degree-hours are therefore filled with 0.0, i.e. "assume a mild day, no
    heating demand". That is a documented assumption, not silent imputation:
    a genuinely cold period with missing weather shows up as a positive
    residual, which the detectors can flag (see docs/methodology.md).
    """
    cols = ["hour", "dow", "hour_of_week", "is_weekend"] + (["hdd"] if "hdd" in df.columns else [])
    X = df[cols].to_numpy(float)
    if np.isnan(X).any():
        X = np.nan_to_num(X, nan=0.0)
    return X, cols


def fit_regression(train: pd.DataFrame, value_col: str = "value") -> Ridge:
    X, _ = design_matrix(train)
    y = train[value_col].to_numpy(float)
    model = Ridge(alpha=1.0).fit(X, y)
    return model


def fit_gbm(train: pd.DataFrame, value_col: str = "value", seed: int = 7) -> HistGradientBoostingRegressor:
    X, _ = design_matrix(train)
    y = train[value_col].to_numpy(float)
    model = HistGradientBoostingRegressor(max_iter=200, random_state=seed).fit(X, y)
    return model


def predict(model: object, df: pd.DataFrame) -> np.ndarray:
    X, _ = design_matrix(df)
    return np.asarray(model.predict(X), dtype=float)  # type: ignore[union-attr]


def cvrmse_nmbe(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, float)
    y_pred = np.asarray(y_pred, float)
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mean = float(np.mean(np.abs(y_true))) or 1.0
    return {"cvrmse": rmse / mean, "nmbe": float(np.mean(y_true - y_pred)) / mean}


def rolling_origin_scores(
    df: pd.DataFrame,
    fit_fn: object,
    value_col: str = "value",
    n_folds: int = 3,
    train_days: int = 28,
) -> list[dict[str, float]]:
    """Expanding train window, 7-day test chunks (time-series CV, no shuffling)."""
    d = df.sort_values("ts_utc").reset_index(drop=True)
    ts = pd.to_datetime(d["ts_utc"], utc=True)
    end = ts.max()
    out = []
    for k in range(n_folds):
        cut = end - pd.Timedelta(days=7 * (n_folds - k))
        tr_start = cut - pd.Timedelta(days=train_days)
        tr = d[(ts >= tr_start) & (ts < cut)]
        te = d[(ts >= cut) & (ts < cut + pd.Timedelta(days=7))]
        if len(tr) < 48 or len(te) < 24:
            continue
        model = fit_fn(tr, value_col)  # type: ignore[operator]
        pred = predict(model, te)
        out.append(cvrmse_nmbe(te[value_col].to_numpy(float), pred))
    return out
