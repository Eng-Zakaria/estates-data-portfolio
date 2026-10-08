"""Measure how well the P16 thresholds separate planted faults from normal meters.

Run from the repo root:

    python projects/p16-energy-anomaly/scripts/threshold_separation.py

This script exists because the threshold justification in docs/methodology.md
must be checkable, and because one of those claims turned out to be false on
the default profile (see the OUTPUT section and docs/methodology.md section 3).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly.detectors import overnight_drift, overnight_ratio  # noqa: E402

PLANTED_METERS = {"M-B007-E01", "M-B019-G01", "M-B015-E01"}
PROFILES = {"small": Path("data/truth"), "default": Path("data/p16_default")}
OOH_THRESHOLD = 0.5
DRIFT_THRESHOLD_FRAC = 0.08


def measure(root: Path) -> pd.DataFrame:
    readings = pd.read_parquet(root / "meter_readings_hh.parquet")
    meta = pd.read_parquet(root / "meters.parquet")[["meter_id", "building_id", "utility"]]
    d = readings.merge(meta, on="meter_id")
    d["ts_utc"] = pd.to_datetime(d["ts_utc"], utc=True)
    rows: list[dict[str, object]] = []
    for meter_id, grp in d.groupby("meter_id"):
        v = pd.to_numeric(grp["value"], errors="coerce").to_numpy(float)
        if np.isfinite(v).sum() == 0:
            continue
        ts = grp["ts_utc"].reset_index(drop=True)
        hod = ts.dt.hour
        peak = float(np.nanpercentile(v, 99))
        ratio = overnight_ratio(pd.Series(v), hod, peak)
        # replicate the overnight-drift numerator so the separation can be seen
        n = len(v)
        window = max(48, min(1344, n // 4))
        night = (hod.to_numpy() >= 0) & (hod.to_numpy() < 5)
        first = v[:window][night[:window]]
        last = v[n - window :][night[n - window :]]
        first = first[np.isfinite(first)]
        last = last[np.isfinite(last)]
        usable = len(first) > 24 and len(last) > 24 and peak > 0
        diff_frac = float((last.mean() - first.mean()) / peak) if usable else np.nan
        rows.append(
            {
                "meter_id": meter_id,
                "building_id": grp["building_id"].iloc[0],
                "utility": grp["utility"].iloc[0],
                "ooh_ratio": round(ratio, 3),
                "ooh_flag": bool(ratio > OOH_THRESHOLD),
                "night_diff_frac_of_peak": round(diff_frac, 4) if np.isfinite(diff_frac) else np.nan,
                "drift_flag": bool(overnight_drift(v, ts, peak)),
                "planted": meter_id in PLANTED_METERS,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    for name, root in PROFILES.items():
        if not (root / "meter_readings_hh.parquet").exists():
            print(f"=== {name}: {root} not built, skipping")
            continue
        df = measure(root)
        el = df[df.utility == "electricity"]
        normal = el[~el.planted]
        planted = el[el.planted]
        print(f"=== {name} profile: {len(df)} meters, {len(el)} electricity, {len(normal)} normal electricity")
        print(f"  overnight ratio  normal max {normal.ooh_ratio.max()} / median {normal.ooh_ratio.median()}")
        print(f"                  planted {planted.ooh_ratio.tolist()}")
        print(
            f"  ooh_flag (>{OOH_THRESHOLD})      true positives "
            f"{int((planted.ooh_flag).sum())} / {len(planted)}   "
            f"false positives {int(normal.ooh_flag.sum())} / {len(normal)}"
        )
        print(f"  night diff/peak normal max {normal.night_diff_frac_of_peak.max()}")
        print(f"                  planted {planted.night_diff_frac_of_peak.tolist()}")
        print(
            f"  drift_flag       true positives {int(planted.drift_flag.sum())} / {len(planted)}   "
            f"false positives {int(normal.drift_flag.sum())} / {len(normal)}"
        )
        print(
            f"  verdict: ooh threshold {'separates' if int(normal.ooh_flag.sum()) == 0 else 'DOES NOT separate'} "
            f"on this profile"
        )
        print()


if __name__ == "__main__":
    main()
