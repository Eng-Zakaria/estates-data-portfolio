"""Apply the P15 validation contract to a readings frame.

This is the Python reference for what the Node-RED flow does at runtime:
route each message to `accepted` or `dead_letter` with a reason code, then
summarise. Used by tests and by `scripts/ingest_local.py` so the offline path
and the Node-RED path agree on outcomes.

    python src/ingest_contract.py --readings data/p15/bms_readings_sim.parquet --out data/p15
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from validate import Validator

REPO = Path(__file__).resolve().parent.parent


def _text(value: object) -> str | None:
    """A row attribute as text, or None when the column is absent or null.

    itertuples types an attribute as whatever the column can hold, so this
    narrows the two identifier columns once per row.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return str(value)


def apply_contract(
    readings: pd.DataFrame, validator: Validator | None = None, *, now: pd.Timestamp | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split raw messages into accepted readings and dead-letter rows.

    `readings` needs ts, value, unit, quality and a point identifier. The
    identifier may be a wire `topic` or a canonical `point_id`: a replay from
    the lakehouse export carries the latter, so both are accepted.
    Returns (accepted, dead_letter) where dead_letter has topic, payload, reason.
    """
    validator = validator or Validator.from_repo(REPO)
    now_ts = pd.Timestamp(now) if now is not None else None
    id_to_topic = {row["point_id"]: row["topic"] for row in validator.registry.values()}

    accepted: list[dict[str, object]] = []
    dead: list[dict[str, object]] = []
    for row in readings.itertuples():
        topic = _text(getattr(row, "topic", None))
        if topic is None:
            topic = id_to_topic.get(_text(getattr(row, "point_id", None)) or "")
        quality = getattr(row, "quality", None)
        unit = getattr(row, "unit", None)
        # the dry-run file stores values as strings (malformed payloads are
        # genuinely non-numeric), so coerce numerics and leave the rest alone
        raw_value = row.value
        if isinstance(raw_value, str):
            try:
                raw_value = float(raw_value)
            except ValueError:
                pass
        payload: dict[str, object] = {"ts": row.ts, "value": raw_value}
        if quality is not None and not (isinstance(quality, float) and pd.isna(quality)):
            payload["quality"] = quality
        if unit is not None:
            payload["unit"] = unit
        # simulate the wire payload: malformed rows genuinely lack `quality`
        raw = json.dumps(payload)
        result = validator.check(topic or "", raw, now=now_ts.to_pydatetime() if now_ts is not None else None)
        if result.ok and result.ts is not None and result.value is not None:
            accepted.append(
                {
                    "ts": result.ts.isoformat(),
                    "point_id": result.point_id,
                    "value": result.value,
                    "unit": result.unit,
                    "quality": result.quality,
                }
            )
        else:
            dead.append({"topic": topic, "payload": raw, "reason": result.reason or "UNKNOWN", "ts": row.ts})
    return pd.DataFrame(accepted), pd.DataFrame(dead)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readings", type=Path, default=Path("data/p15/bms_readings_sim.parquet"))
    parser.add_argument("--out", type=Path, default=Path("data/p15"))
    args = parser.parse_args()

    raw = pd.read_parquet(args.readings)
    # the simulator clock starts at wall-clock now; validate against the frame
    # max timestamp so future-skew checks reflect the simulated run
    accepted, dead = apply_contract(raw, now=pd.Timestamp(raw["ts"].max()) + pd.Timedelta(minutes=1))
    args.out.mkdir(parents=True, exist_ok=True)
    accepted.to_parquet(args.out / "bms_readings_accepted.parquet", index=False)
    dead.to_parquet(args.out / "bms_dead_letter.parquet", index=False)

    total = len(raw)
    valid = total - len(dead)
    # two rates, because they answer different questions: the first is the
    # pipeline's loss rate (messages a lossless link should have delivered), the
    # second is its share of everything the simulator sent, malformed included
    valid_rate = len(accepted) / valid if valid else 0.0
    overall_rate = len(accepted) / total if total else 0.0
    print(f"messages: {total}")
    print(f"valid: {valid}")
    print(f"accepted: {len(accepted)} ({valid_rate:.4%} of valid, {overall_rate:.4%} of all)")
    print(f"dead-letter: {len(dead)}")
    if not dead.empty:
        print("\nreasons:")
        for reason, count in dead["reason"].value_counts().items():
            print(f"  {reason}: {count}")


if __name__ == "__main__":
    main()
