"""Evaluation: inject ≥200 labelled anomalies into held-out series; score methods.

Anomaly types mirror the fault typology; each injection records type,
magnitude, start, duration. Detection delay = first flag offset in periods.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import detectors
from .cleaning import flag_flatline

TYPES = ["step", "drift", "spike", "flatline", "ooh", "missing"]


def inject(
    values: np.ndarray,
    rng: np.random.Generator,
    n: int = 48,
    seed_types: bool = True,
    protect_head: int = 0,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Return (corrupted series, truth table with type/start/duration/magnitude).

    Injections are SPARSE and NON-OVERLAPPING (≥12 clean periods apart) inside
    `[protect_head, n_periods)`, so the robust scale estimators the detectors
    rely on are not themselves corrupted. `protect_head` keeps a clean training
    window for baseline fitting (M&V practice: baseline on clean history).
    Deterministic given the rng seed.
    """
    v = np.asarray(values, float).copy()
    n_periods = len(v)
    truth = []
    scale = np.median(np.abs(v[np.isfinite(v)])) or 1.0
    occupied: list[tuple[int, int]] = []

    def free(start: int, dur: int, margin: int = 12) -> bool:
        s, e = start - margin, start + dur + margin
        return all(e <= os or s >= oe for os, oe in occupied)

    order = [TYPES[i % len(TYPES)] if seed_types else str(rng.choice(TYPES)) for i in range(n)]
    rng.shuffle(order)
    for kind in order:
        dur = int(rng.integers(2, 96))
        for _ in range(200):  # rejection sample a free slot
            start = int(rng.integers(protect_head, max(protect_head + 1, n_periods - dur)))
            if free(start, dur):
                break
        else:
            continue  # series too crowded; skip rather than overlap
        mag = float(rng.uniform(0.5, 3.0)) * scale
        if kind == "step":
            # Real schedule/plant steps go both directions; keep them smaller
            # than waste-type magnitudes so stacked steps do not drown the
            # series (a saturated series makes robust scales meaningless).
            mag = float(rng.uniform(0.5, 1.5)) * scale * float(rng.choice([-1.0, 1.0]))
            v[start:] += mag
        elif kind == "drift":
            v[start : start + dur] += np.linspace(0, mag, dur)
        elif kind == "spike":
            v[start : start + min(dur, 4)] += mag * 3
        elif kind == "flatline":
            v[start : start + dur] = v[start]
        elif kind == "ooh":
            v[start : start + dur] += mag * 0.8
        elif kind == "missing":
            v[start : start + dur] = np.nan
        # Steps persist past their window, but later non-overlapping events
        # still carry valid truth rows (windows never overlap), so occupancy
        # only blocks the event window itself.
        occupied.append((start, start + dur))
        truth.append({"type": kind, "start": start, "duration": dur, "magnitude": round(mag, 3)})
    # Meters cannot read negative; clip (documented; may create short flat runs).
    v = np.maximum(v, 0.0)
    return v, pd.DataFrame(truth)


def score_flags(flags: np.ndarray, truth: pd.DataFrame, tolerance: int = 6) -> dict[str, dict[str, float]]:
    """Per-type precision/recall/F1 + mean detection delay (periods)."""
    flags = np.asarray(flags, dtype=bool)
    out: dict[str, dict[str, float]] = {}
    for kind, grp in truth.groupby("type"):
        tp = 0
        delays = []
        matched = np.zeros(len(flags), dtype=bool)
        for _, row in grp.iterrows():
            s, e = int(row["start"]), int(row["start"]) + int(row["duration"]) + tolerance
            window = flags[s:e]
            if window.any():
                tp += 1
                delays.append(int(np.argmax(window)))
                matched[s:e] |= window
            # false positives counted globally below
        flagged_outside = int(flags.sum() - matched.sum())
        fp = max(0, flagged_outside // max(1, len(grp)))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / len(grp) if len(grp) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        out[str(kind)] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "mean_delay_periods": round(float(np.mean(delays)) if delays else -1, 1),
            "n": int(len(grp)),
        }
    return out


def run_detectors(df: pd.DataFrame, residual: np.ndarray, seed: int = 7) -> dict[str, np.ndarray]:
    values = pd.to_numeric(df["value"], errors="coerce").to_numpy(float)
    flat = flag_flatline(pd.Series(values)).to_numpy()
    return {
        "mad": detectors.mad_zscore(residual),
        "isolation_forest": detectors.isolation_forest_flags(df, residual, seed=seed),
        "cusum": detectors.cusum_flags(residual),
        "flatline": flat,
        "missing": pd.isna(values),
    }
