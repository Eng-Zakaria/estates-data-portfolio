"""Export P15 readings to the P01 `bms_trends` wide-CSV contract.

The TimescaleDB store is the operational system of record; the lakehouse in P01
consumes a nightly file instead, so the export has to match the contract that
P01 already validates (`platform/contracts/bms_trends.yml`):

* filename `bms_trends_YYYYMMDD.csv`
* first column `timestamp`, ISO-8601 **with offset** (`%Y-%m-%dT%H:%M:%S%z`)
* one column per point, named `<point_id> [<unit>]` so the unit travels with the header
* missing cells written as the literal string `N/A` (P01 quarantines those as
  `nulls_in_mandatory`, which is the intended behaviour, not an error)

Usage (offline, from the accepted Parquet):

    python src/export_bms_trends.py --readings data/p15/bms_readings_accepted.parquet --out data/raw

Usage (live stack, no Python needed - see sql/export_bms_trends.sql):

    docker compose exec -T timescaledb psql -U bms_user -d bms_db -f /sql/export_bms_trends.sql
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from validate import load_registry

REPO = Path(__file__).resolve().parent.parent
REGISTRY_CSV = Path(__file__).resolve().parent / "point_registry.csv"
LOCAL_TZ = "Europe/London"
TS_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
NA = "N/A"


def to_wide(
    readings: pd.DataFrame,
    registry: dict[str, dict[str, str]] | None = None,
    *,
    tz: str = LOCAL_TZ,
    round_to: int = 3,
) -> pd.DataFrame:
    """Pivot validated readings into the P01 wide shape.

    `readings` needs columns ts, point_id, value (as produced by
    `ingest_contract.apply_contract` or read back from `bms.readings`).
    Timestamps are converted to `tz` before formatting so the offset in the file
    matches the site's local clock; points absent from the registry fall back to
    the unit recorded on the reading itself, then to an empty unit.
    """
    registry = registry if registry is not None else load_registry(str(REGISTRY_CSV))
    frame = readings.copy()
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    # coerce through object: dead-lettered readings reach here carrying the
    # original non-numeric string, and a float column refuses that assignment
    frame["value"] = pd.to_numeric(frame["value"].astype(object), errors="coerce")
    frame = frame.dropna(subset=["ts", "value"])
    if frame.empty:
        return pd.DataFrame(columns=["timestamp"])

    # keep the last delivery for a (ts, point_id) pair, matching the database's
    # idempotent upsert on re-delivery
    frame = frame.sort_values("ts").drop_duplicates(subset=["ts", "point_id"], keep="last")
    wide = frame.pivot_table(index="ts", columns="point_id", values="value", aggfunc="last")
    wide = wide.round(round_to)

    # unit from the reading itself when present, else from the point registry
    units: dict[str, str] = {}
    if "unit" in frame.columns:
        from_readings = frame.drop_duplicates("point_id").set_index("point_id")["unit"]
        units.update({pid: (u or "") for pid, u in from_readings.items() if isinstance(u, str) and u})
    for pid, row in registry.items():
        units.setdefault(pid, row.get("unit") or "")

    wide.index = pd.DatetimeIndex(wide.index).tz_convert(tz).strftime(TS_FORMAT)
    wide.index.name = "timestamp"
    wide = wide.rename(columns=lambda pid: f"{pid} [{units.get(pid, '')}]")

    # cells with no reading for that timestamp become the literal N/A string;
    # cast to object first so pandas does not warn about mixed dtypes
    wide = wide.astype(object).where(wide.notna(), NA)
    return wide.reset_index()


def write_bms_trends(
    readings: pd.DataFrame,
    out_dir: Path,
    *,
    date_stamp: date | None = None,
    tz: str = LOCAL_TZ,
    registry: dict[str, dict[str, str]] | None = None,
) -> Path:
    """Write `bms_trends_YYYYMMDD.csv` into out_dir; returns the path."""
    wide = to_wide(readings, registry, tz=tz)
    if wide.empty or len(wide) == 1 and "timestamp" not in wide.columns:
        raise ValueError("no readings to export")
    stamp = date_stamp or pd.to_datetime(wide["timestamp"].iloc[0], utc=True).tz_localize(None).date()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"bms_trends_{stamp.strftime('%Y%m%d')}.csv"
    wide.to_csv(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readings", type=Path, default=Path("data/p15/bms_readings_accepted.parquet"))
    parser.add_argument("--out", type=Path, default=Path("data/raw"), help="P01 raw landing zone")
    parser.add_argument("--tz", default=LOCAL_TZ)
    args = parser.parse_args()

    readings = pd.read_parquet(args.readings)
    path = write_bms_trends(readings, args.out, tz=args.tz)
    frame = pd.read_csv(path)
    points = [c for c in frame.columns if c != "timestamp"]
    na_cells = int((frame[points] == NA).sum().sum()) if points else 0
    print(f"{len(frame)} timestamps x {len(points)} points -> {path}")
    print(f"N/A cells (P01 quarantines these as nulls_in_mandatory): {na_cells}")


if __name__ == "__main__":
    main()