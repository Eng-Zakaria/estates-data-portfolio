"""P02 demo helper: drop a good file and a corrupted file into the landing zone.

Usage (host):
    python platform/orchestration/scripts/demo_drop.py --scenario good|corrupt|both
Good files are copied from data/raw; corrupt files are byte-truncated copies.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "raw"
LANDING = REPO / "data" / "landing"

GOOD = {
    "cafm_workorders": "cafm_workorders_*.csv",
    "meter_hh_supplierA": "meter_hh_supplierA_*.csv",
}


def drop_good(source: str) -> str:
    LANDING.mkdir(parents=True, exist_ok=True)
    candidates = sorted(RAW.glob(GOOD[source]))
    if not candidates:
        raise SystemExit(f"no raw files for {source}; run `make data` first")
    dest = LANDING / f"{candidates[0].stem}_demo{candidates[0].suffix}"
    shutil.copy(candidates[0], dest)
    print(f"good file -> {dest}")
    return str(dest)


def drop_corrupt(source: str) -> str:
    LANDING.mkdir(parents=True, exist_ok=True)
    candidates = sorted(RAW.glob(GOOD[source]))
    if not candidates:
        raise SystemExit(f"no raw files for {source}; run `make data` first")
    raw = candidates[0].read_bytes()
    dest = LANDING / f"{candidates[0].stem}_corrupt{candidates[0].suffix}"
    # Truncate mid-row + inject an unknown column header => drift + parse failure.
    head, _, _rest = raw.partition(b"\n")
    dest.write_bytes(head + b",Mystery_Column\n" + raw[len(head) + 1 : len(head) // 2])
    print(f"corrupt file -> {dest}")
    return str(dest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["good", "corrupt", "both"], default="both")
    args = ap.parse_args()
    if args.scenario in ("good", "both"):
        drop_good("cafm_workorders")
    if args.scenario in ("corrupt", "both"):
        drop_corrupt("meter_hh_supplierA")


if __name__ == "__main__":
    main()
