"""Injection study only (fast iteration; full `make eval` also builds the board)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("projects/p16-energy-anomaly/src").absolute()))

import numpy as np

from anomaly.baselines import apply_median_profile, baseline_median_profile
from anomaly.data_campus import DEFAULT_CACHE, load_campus
from anomaly.evaluate import inject, run_detectors, score_flags

SEED = 7

rng = np.random.default_rng(SEED)
df, _ = load_campus(truth_dir=DEFAULT_CACHE)
series = df[df.meter_id == "M-B001-E01"].sort_values("ts_utc").reset_index(drop=True)
base = series["value"].to_numpy(float)
corrupted, truth = inject(base, rng, n=210, protect_head=90 * 48)
hold_c = series.copy()
hold_c["value"] = corrupted
prof = baseline_median_profile(hold_c.iloc[: 90 * 48])
residual = hold_c["value"].to_numpy(float) - apply_median_profile(hold_c, prof)
methods = run_detectors(hold_c[["ts_utc", "value"]], residual, seed=SEED)
scores = {name: score_flags(fl, truth) for name, fl in methods.items()}
print("n:", len(truth))
for method, types in scores.items():
    print("===", method)
    for t, s in types.items():
        print(
            f"  {t:9s} P={s['precision']:.3f} R={s['recall']:.3f} "
            f"F1={s['f1']:.3f} delay={s['mean_delay_periods']} n={s['n']}"
        )
