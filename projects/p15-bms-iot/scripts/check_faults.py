"""Measure fault-detection recall against the simulator truth file.

Reads the dry-run simulator output plus `truth.json`, runs `health.detect`,
and reports per-fault recall (detected planted windows / planted windows).
Writes `fault_detection.csv` and prints a markdown table for the README.

    python scripts/check_faults.py --readings data/p15/bms_readings_sim.parquet --truth data/p15/truth.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from health import DetectionConfig, detect  # noqa: E402


def _overlaps(a_start, a_end, b_start, b_end, tolerance_min: float = 15.0) -> bool:
    tol = pd.Timedelta(minutes=tolerance_min)
    return (a_start - tol) <= b_end and (a_end + tol) >= b_start


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readings", type=Path, default=Path("data/p15/bms_readings_sim.parquet"))
    parser.add_argument("--truth", type=Path, default=Path("data/p15/truth.json"))
    parser.add_argument("--out", type=Path, default=Path("projects/p15-bms-iot/docs/fault_detection.csv"))
    parser.add_argument("--tolerance-minutes", type=float, default=15.0)
    args = parser.parse_args()

    readings = pd.read_parquet(args.readings)
    truth = json.loads(args.truth.read_text(encoding="utf-8"))
    config = DetectionConfig(interval_minutes=truth["interval_minutes"])
    findings = detect(readings, config=config)

    rows = []
    for planted in truth["faults"]:
        base = pd.Timestamp(truth["start"])
        start = base + pd.Timedelta(minutes=planted["start_minute"])
        end = base + pd.Timedelta(minutes=planted["end_minute"])
        match = findings[
            (findings["rule_id"] == planted["detection_rule"])
            & (findings["point_id"] == planted["point_id"])
            & (findings["start_ts"] <= end + pd.Timedelta(minutes=args.tolerance_minutes))
            & (findings["end_ts"] >= start - pd.Timedelta(minutes=args.tolerance_minutes))
        ]
        rows.append(
            {
                "fault": planted["fault"],
                "rule_id": planted["detection_rule"],
                "point_id": planted["point_id"],
                "expected_start": start,
                "expected_end": end,
                "detected": not match.empty,
                "detected_start": match["start_ts"].min() if not match.empty else pd.NaT,
                "detected_end": match["end_ts"].max() if not match.empty else pd.NaT,
                "delay_minutes": (
                    round((match["start_ts"].min() - start).total_seconds() / 60, 1) if not match.empty else None
                ),
                "detail": planted["detail"],
            }
        )

    table = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)

    print(f"| fault | rule | planted | detected | recall | mean delay (min) |")
    print("|---|---|---|---|---|---|")
    for fault, grp in table.groupby("fault", sort=True):
        detected = int(grp["detected"].sum())
        delays = grp.loc[grp["detected"], "delay_minutes"]
        mean_delay = round(float(delays.mean()), 1) if len(delays) else None
        print(f"| {fault} | {grp['rule_id'].iloc[0]} | {len(grp)} | {detected} | {detected / len(grp):.0%} | {mean_delay} |")
    total_detected = int(table["detected"].sum())
    print(f"\nOverall recall: {total_detected}/{len(table)} = {total_detected / len(table):.0%}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
