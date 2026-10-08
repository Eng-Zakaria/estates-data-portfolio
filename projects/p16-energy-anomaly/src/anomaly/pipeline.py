"""End-to-end pipeline: baselines -> detectors -> typology -> savings -> action list."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import baselines, detectors
from .baselines import add_time_features, cvrmse_nmbe
from .cleaning import cleaning_report, winsorise_fit
from .config import LOOKBACK_DAYS_BASELINE, MIN_TRAIN_DAYS, OOH_THRESHOLD_PCT_PEAK, SEED
from .evaluate import run_detectors
from .typology import classify_meter, load_factors, savings


def _finite_pairs(y: np.ndarray, y_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Drop periods where either side is NaN so CV scores ignore gaps."""
    ok = np.isfinite(np.asarray(y, float)) & np.isfinite(np.asarray(y_pred, float))
    return np.asarray(y, float)[ok], np.asarray(y_pred, float)[ok]


def _runs(flags: np.ndarray, cap: int = 20) -> list[list[int]]:
    """Merge True runs into [start, end] index pairs (capped)."""
    out: list[list[int]] = []
    i, n = 0, len(flags)
    while i < n:
        if flags[i]:
            j = i
            while j + 1 < n and flags[j + 1]:
                j += 1
            out.append([int(i), int(j)])
            if len(out) >= cap:
                break
            i = j + 1
        else:
            i += 1
    return out


def run_meter(
    df: pd.DataFrame,
    weather: pd.DataFrame | None = None,
    tariff: float = 0.28,
    seed: int = SEED,
) -> dict[str, object]:
    """Analyse one meter's HH series. Returns findings + diagnostics dict."""
    d = df.sort_values("ts_utc").reset_index(drop=True).copy()
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    report = cleaning_report(d)
    finite = d["value"].to_numpy(float)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        # A meter with no readings at all (BDG2 has a few) cannot be analysed.
        # Return a data-quality-only result; no peak, no flags, no savings.
        return {
            "cleaning": report,
            "peak": 0.0,
            "cv": {},
            "n_flags": {
                "mad": 0,
                "isolation_forest": 0,
                "cusum": 0,
                "flatline": 0,
                "missing": int(d["value"].isna().sum()),
                "drift": 0,
            },
            "drift": False,
            "evidence": {"mad": [], "flat_runs": [], "change_points": []},
            "first_flags": {},
            "change_points": [],
            "typology": ["missing_data"],
            "savings": savings(0.0),
            "excess_kwh_day": 0.0,
            "attributed_excess_kwh_day": 0.0,
            "overnight_excess_kwh_day": 0.0,
            "residual_excess_kwh_day": 0.0,
        }
    peak = float(np.nanpercentile(d["value"], 99))
    # attach temperature where available
    if weather is not None:
        w = weather.copy()
        w["ts_utc"] = pd.to_datetime(w["ts_utc"], utc=True)
        d = d.merge(w[["ts_utc", "temp_c"]], on="ts_utc", how="left")
    feat = add_time_features(d, temp_col="temp_c" if "temp_c" in d.columns else None)
    # train on first LOOKBACK days with enough history, test on the rest
    ts = pd.to_datetime(feat["ts_utc"], utc=True)
    split = ts.min() + pd.Timedelta(days=LOOKBACK_DAYS_BASELINE)
    train = feat[ts < split].copy()
    if (ts.max() - ts.min()).days < MIN_TRAIN_DAYS or len(train) < 48:
        train = feat
    # Fit only on rows with a finite reading: BDG2 meters have real gaps and
    # both Ridge and the GBM contract need finite y. Detection still uses the
    # full series, so gaps surface as missing_data flags rather than vanishing.
    fit_mask = np.isfinite(train["value"].to_numpy(float))
    if "temp_c" in train.columns:
        fit_mask &= np.isfinite(train["temp_c"].to_numpy(float))
    if fit_mask.sum() < 48:
        # too few joint reading+weather rows in the training window: fall back to
        # readings only so weather gaps never cost us the baseline entirely
        fit_mask = np.isfinite(train["value"].to_numpy(float))
    train_fit = train[fit_mask].copy()
    if len(train_fit) < 48:
        # training window is effectively empty for this meter (e.g. the first
        # 28 days are all missing): fit on any finite period anywhere
        any_mask = np.isfinite(feat["value"].to_numpy(float))
        train_fit = feat[any_mask].copy()
    y_fit = winsorise_fit(train_fit["value"].to_numpy(float))
    train_fit["value"] = y_fit
    prof = baselines.baseline_median_profile(train_fit)
    pred_a = baselines.apply_median_profile(feat, prof)
    reg = baselines.fit_regression(train_fit if "hdd" in train_fit.columns else train.assign(hdd=0.0))
    pred_b = baselines.predict(reg, feat if "hdd" in feat.columns else feat.assign(hdd=0.0))
    gbm = baselines.fit_gbm(train_fit if "hdd" in train_fit.columns else train.assign(hdd=0.0), seed=seed)
    pred_c = baselines.predict(gbm, feat if "hdd" in feat.columns else feat.assign(hdd=0.0))
    # primary residual: regression (best documented tradeoff); keep others for CV table
    residual = feat["value"].to_numpy(float) - pred_b
    y_all = feat["value"].to_numpy(float)
    cv: dict[str, dict[str, float]] = {}
    for name, pred in (("median_profile", pred_a), ("regression", pred_b), ("gbm", pred_c)):
        pairs = _finite_pairs(y_all, pred)
        if len(pairs[0]) == 0:
            cv[name] = {"cvrmse": float("nan"), "nmbe": float("nan")}
        else:
            cv[name] = cvrmse_nmbe(*pairs)
    flags = run_detectors(feat[["ts_utc", "value"]], residual, seed=seed)
    cps = detectors.mean_shift_scan(feat["value"].to_numpy(float))
    utility = str(df["utility"].iloc[0]) if "utility" in df.columns else "electricity"
    drift = bool(
        detectors.overnight_drift(feat["value"].to_numpy(float), feat["ts_utc"], peak) and utility == "electricity"
    )
    types = classify_meter(feat, flags, cps, peak, OOH_THRESHOLD_PCT_PEAK, drift)
    # overnight excess kWh/day for savings
    hod = feat["hour"].to_numpy()
    night_mean = float(np.nanmean(feat["value"].to_numpy(float)[(hod >= 0) & (hod < 5)]))
    day_peak = peak
    overnight_excess = max(0.0, (night_mean - 0.2 * day_peak)) * 5  # 5 overnight hours
    # residual excess: sustained over-consumption vs baseline (e.g. summer heating).
    # Only residuals above 3 robust sd count, so symmetric noise does not
    # manufacture phantom savings on clean meters. Annualised over series days.
    resid = residual[np.isfinite(residual)]
    mad = float(np.median(np.abs(resid - np.median(resid)))) if len(resid) else 0.0
    sigma = 1.4826 * mad if mad > 0 else float(np.std(resid)) if len(resid) else 1.0
    n_days = max(
        1.0,
        (
            pd.to_datetime(feat["ts_utc"], utc=True).max() - pd.to_datetime(feat["ts_utc"], utc=True).min()
        ).total_seconds()
        / 86400,
    )
    residual_excess = float(np.maximum(0.0, resid - 3 * sigma).sum()) / n_days
    # Overnight baseload waste is an electricity-HVAC pattern; gas savings come
    # from baseline deviation only (night heating in winter is legitimate).
    excess_day = max(overnight_excess, residual_excess) if utility == "electricity" else residual_excess
    factors = load_factors()
    # Attributed savings: only fault modes flagged on THIS meter contribute.
    # Normal baseload is an efficiency opportunity, not an exception, so it
    # carries no savings here (keeps the exceptions list specific). A stuck or
    # gappy meter cannot have its use estimated: savings £0, data-quality flag.
    attributed = 0.0
    if "high_overnight_baseload" in types:
        attributed += overnight_excess
    if {"spike", "step_change", "gradual_drift"} & set(types):
        attributed += residual_excess
    save = savings(
        attributed,
        kgco2e_per_kwh=factors.get("electricity" if utility == "electricity" else "natural_gas", 0.2),
        tariff_gbp=tariff,
    )
    return {
        "cleaning": report,
        "peak": peak,
        "cv": cv,
        "n_flags": {k: int(np.asarray(v).sum()) for k, v in flags.items()} | {"drift": int(drift)},
        "drift": bool(drift),
        "evidence": {
            "mad": [int(i) for i in np.where(np.asarray(flags["mad"]))[0][:500]],
            "flat_runs": _runs(np.asarray(flags["flatline"])),
            "change_points": [int(i) for i in cps[:10]],
        },
        "first_flags": {
            k: (
                pd.to_datetime(feat["ts_utc"].iloc[int(np.argmax(v))], utc=True).isoformat()
                if bool(np.asarray(v).any())
                else None
            )
            for k, v in flags.items()
        },
        "change_points": [pd.to_datetime(feat["ts_utc"].iloc[i], utc=True).isoformat() for i in cps[:5]],
        "typology": types,
        "savings": save,
        "excess_kwh_day": round(excess_day, 2),
        "attributed_excess_kwh_day": round(attributed, 2),
        "overnight_excess_kwh_day": round(overnight_excess, 2),
        "residual_excess_kwh_day": round(residual_excess, 2),
    }
