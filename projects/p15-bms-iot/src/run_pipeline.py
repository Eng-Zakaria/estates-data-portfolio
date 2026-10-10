"""P15 end-to-end offline pipeline: simulate -> validate -> detect -> export.

Runs the whole chain with no broker, so the demo, the tests and the acceptance
evidence all execute the same code path as the live stack (the only difference
is that MQTT and the database are replaced by Parquet files).

    python src/run_pipeline.py --duration-hours 24 --out data/p15 --raw data/raw
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from export_bms_trends import LOCAL_TZ, write_bms_trends
from health import DetectionConfig, detect, health_summary
from ingest_contract import apply_contract
from simulator import Simulator
from validate import Validator

REPO = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class PipelineResult:
    raw: pd.DataFrame
    accepted: pd.DataFrame
    dead_letter: pd.DataFrame
    findings: pd.DataFrame
    health: pd.DataFrame
    # the truth file mixes counts, strings and nested fault records
    truth: dict[str, Any]
    export_path: Path | None

    @property
    def valid_messages(self) -> int:
        """Messages that were well formed, i.e. what a lossless link must deliver."""
        malformed = self.truth.get("messages_malformed", 0)
        return len(self.raw) - (malformed if isinstance(malformed, int) else 0)

    @property
    def acceptance_rate(self) -> float:
        valid = self.valid_messages
        return len(self.accepted) / valid if valid else 0.0


def run(
    *,
    start: datetime,
    duration_hours: float = 24.0,
    interval_minutes: int = 5,
    seed: int = 42,
    faults: list[str] | None = None,
    out_dir: Path,
    raw_dir: Path | None = None,
) -> PipelineResult:
    sim = Simulator(start, seed=seed, interval_minutes=interval_minutes, faults=faults)
    raw, truth = sim.generate(duration_hours)

    validator = Validator.from_repo(REPO)
    accepted, dead = apply_contract(raw, validator, now=pd.Timestamp(raw["ts"].max()) + pd.Timedelta(minutes=1))

    cfg = DetectionConfig(interval_minutes=interval_minutes)
    findings = detect(accepted, REPO / "src" / "point_registry.csv", cfg)
    health = health_summary(accepted, REPO / "src" / "point_registry.csv", cfg)

    out_dir.mkdir(parents=True, exist_ok=True)
    raw.assign(value=raw["value"].astype(str)).to_parquet(out_dir / "bms_readings_sim.parquet", index=False)
    accepted.to_parquet(out_dir / "bms_readings_accepted.parquet", index=False)
    dead.to_parquet(out_dir / "bms_dead_letter.parquet", index=False)
    findings.to_parquet(out_dir / "bms_findings.parquet", index=False)
    health.to_parquet(out_dir / "bms_point_health.parquet", index=False)
    (out_dir / "truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")

    export_path = write_bms_trends(accepted, raw_dir) if raw_dir else None
    return PipelineResult(raw, accepted, dead, findings, health, truth, export_path)


def summarise(result: PipelineResult) -> str:
    truth = result.truth
    lines = [
        f"points:                {truth['points']}",
        f"messages simulated:    {len(result.raw)}",
        f"  dropped (comms):     {truth['messages_dropped_comms_dropout']}",
        f"  malformed injected:  {truth['messages_malformed']}",
        f"valid messages:        {result.valid_messages}",
        f"accepted:              {len(result.accepted)} ({result.acceptance_rate:.4%} of valid)",
        f"dead letter:           {len(result.dead_letter)}",
    ]
    if not result.dead_letter.empty:
        counts = ", ".join(f"{r}={n}" for r, n in result.dead_letter["reason"].value_counts().items())
        lines.append(f"  reasons:             {counts}")
    lines.append(f"findings:              {len(result.findings)}")
    if not result.findings.empty:
        counts = ", ".join(f"{r}={n}" for r, n in result.findings["rule_id"].value_counts().sort_index().items())
        lines.append(f"  rules:               {counts}")
    unhealthy = result.health[~result.health["healthy"]]
    lines.append(f"unhealthy points:      {len(unhealthy)} of {len(result.health)}")
    if result.export_path:
        lines.append(f"bms_trends export:     {result.export_path}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/p15"))
    parser.add_argument("--raw", type=Path, default=None, help="also write the P01 bms_trends file here")
    parser.add_argument("--duration-hours", type=float, default=24.0)
    parser.add_argument("--interval-minutes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--faults",
        nargs="*",
        default=None,
        help="fault types to inject (default: all); pass no values for a clean-plant run",
    )
    parser.add_argument("--start", default=None, help="ISO start timestamp (default: now, UTC)")
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start) if args.start else datetime.now(UTC).replace(microsecond=0, second=0)
    if args.start is None:
        # fault windows are minutes from the run start and the comments in
        # FAULT_WINDOWS name clock times, so default to midnight local time
        local_now = datetime.now(UTC).astimezone(ZoneInfo(LOCAL_TZ))
        start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    result = run(
        start=start,
        duration_hours=args.duration_hours,
        interval_minutes=args.interval_minutes,
        seed=args.seed,
        faults=args.faults,
        out_dir=args.out,
        raw_dir=args.raw,
    )
    print(summarise(result))


if __name__ == "__main__":
    main()
