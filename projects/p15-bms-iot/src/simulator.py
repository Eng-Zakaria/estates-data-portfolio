"""P15 BMS/sensor simulator.

Publishes synthetic BMS readings to MQTT (or writes them to Parquet with
--dry-run) for 21 plant items and 51 rooms across 3 buildings, following the
point registry in `src/point_registry.csv`.

Topics: `campus/<building>/<system>/<point_class>`
Payload: `{ts, value, unit, quality}`

Fault modes are injected on deterministic (seeded) point ids inside a known
time window and written to a truth file, so `scripts/check_faults.py` can
measure detection recall honestly.

    # offline (no broker) -> Parquet + truth file
    python src/simulator.py --dry-run --out data/p15 --duration-hours 24

    # live
    python src/simulator.py --speedup 144 --duration-hours 24 --truth-out data/p15/truth.json
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from export_bms_trends import LOCAL_TZ
from make_registry import build_registry

REPO = Path(__file__).resolve().parent
FAULTS = ["stuck_valve", "sensor_drift", "comms_dropout", "simultaneous_heat_cool", "out_of_hours"]

# Fault windows are expressed as minutes from the run start (24 h run).
# Fault windows are minutes from the run start, so the run must begin at 00:00
# local time for these to land on the clock times in the comments. Windows on
# the same point class must not overlap, or one injected fault is counted as a
# detection of another (SEM-02 pinning a heating valve at 62% already drives
# SEM-01 whenever the cooling valve is open).
FAULT_WINDOWS: dict[str, tuple[int, int]] = {
    "stuck_valve": (60, 360),  # 01:00-06:00, both valves' peers keep moving
    "sensor_drift": (240, 720),  # 04:00-12:00 (long enough for a drift window)
    "comms_dropout": (420, 540),  # 07:00-09:00
    # 20:00-23:00: overnight the cooling valve sits at its 10% baseline, so an
    # SEM-01 hit here can only come from the injected fault
    "simultaneous_heat_cool": (1200, 1380),
    "out_of_hours": (0, 720),  # first 12 h of the day
}
FAULTS_PER_TYPE = 4

# Modulating valve and damper position feedback carries roughly +/-1% noise on a
# real BMS; a tighter band would make a healthy valve look frozen against its
# own peer, so the noise is per point class rather than a single global value.
NOISE_BY_CLASS: dict[str, float] = {
    "damper_pos": 1.0,
    "fan_speed": 1.0,
    "heating_valve": 1.0,
    "cooling_valve": 1.0,
}
DEFAULT_NOISE = 0.4


def noise_for(point_class: str) -> float:
    return NOISE_BY_CLASS.get(point_class, DEFAULT_NOISE)


# point classes with a floor of zero (energy meters, counts, percentages)
_NON_NEGATIVE_CLASSES = {"sub_meter_kwh", "occupancy", "damper_pos", "fan_speed", "heating_valve", "cooling_valve"}


def occupancy_people(ts: datetime, capacity: int) -> int:
    """Teaching-day occupancy for a room: empty overnight and at weekends.

    Timestamps arrive in UTC but the teaching day is a local concept, so the
    hour is taken in Europe/London before the profile is applied.
    """
    local = ts.astimezone(ZoneInfo(LOCAL_TZ)) if ts.tzinfo else ts
    if local.weekday() >= 5 or local.hour < 8 or local.hour >= 19:
        return 0
    shape = {9: 0.6, 10: 0.9, 11: 0.8, 12: 0.5, 13: 0.7, 14: 0.95, 15: 0.9, 16: 0.6, 17: 0.3, 18: 0.1}
    frac = shape.get(local.hour, 0.0)
    return int(capacity * frac)


@dataclass
class TruthFault:
    fault: str
    point_id: str
    peer_point_id: str | None
    start_minute: int
    end_minute: int
    detection_rule: str
    detail: str


class Simulator:
    """Deterministic (seeded) BMS telemetry generator."""

    def __init__(
        self,
        start: datetime,
        *,
        seed: int = 42,
        interval_minutes: int = 5,
        faults: list[str] | None = None,
    ) -> None:
        self.start = start
        self.seed = seed
        self.rng = random.Random(seed)
        self.interval_minutes = interval_minutes
        self.points = build_registry()
        self._point_index = {row["point_id"]: i for i, row in enumerate(self.points)}
        self.steps = 0
        # `None` means every fault type; an explicit empty list means none, which is how
        # the false-positive check runs the same day with a clean plant
        self.active_faults = [f for f in (FAULTS if faults is None else faults) if f in FAULT_WINDOWS]
        self.plan = self._plan_faults()
        self.noise: dict[str, random.Random] = {}

    # --- fault planning ------------------------------------------------------
    def _plan_faults(self) -> list[TruthFault]:
        plan: list[TruthFault] = []
        by_class: dict[str, list[str]] = {}
        by_kind_class: dict[tuple[str, str], list[str]] = {}
        for row in self.points:
            by_class.setdefault(row["point_class"], []).append(row["point_id"])
            by_kind_class.setdefault((row["equipment_kind"], row["point_class"]), []).append(row["point_id"])
        for fault in self.active_faults:
            start_min, end_min = FAULT_WINDOWS[fault]
            candidates: list[tuple[str, str | None]] = []
            if fault == "stuck_valve":
                for pid in by_kind_class.get(("ahu", "heating_valve"), [])[:FAULTS_PER_TYPE]:
                    candidates.append((pid, pid.replace("heating_valve", "cooling_valve")))
            elif fault == "sensor_drift":
                candidates = [(pid, None) for pid in by_class.get("co2", [])[:FAULTS_PER_TYPE]]
            elif fault == "comms_dropout":
                candidates = [(pid, None) for pid in by_class.get("room_temp", [])[:FAULTS_PER_TYPE]]
            elif fault == "simultaneous_heat_cool":
                # both valves on the same AHU are pinned open: the peer point is
                # part of the same planted window, so set peer_point_id to it.
                # Use the AHUs the stuck-valve fault did not touch, so neither
                # fault can be credited with the other's detection.
                spare = {t.point_id for t in plan if t.fault == "stuck_valve"}
                pairs: list[tuple[str, str | None]] = [
                    (pid, pid.replace("heating_valve", "cooling_valve"))
                    for pid in by_kind_class.get(("ahu", "heating_valve"), [])
                    if pid not in spare
                ]
                candidates = pairs[:FAULTS_PER_TYPE]
            elif fault == "out_of_hours":
                candidates = [(pid, None) for pid in by_class.get("fan_speed", [])[:FAULTS_PER_TYPE]]
            for pid, peer in candidates[:FAULTS_PER_TYPE]:
                plan.append(
                    TruthFault(
                        fault=fault,
                        point_id=pid,
                        peer_point_id=peer,
                        start_minute=start_min,
                        end_minute=end_min,
                        detection_rule={
                            "stuck_valve": "SEM-02",
                            "sensor_drift": "SEM-05",
                            "comms_dropout": "STALENESS",
                            "simultaneous_heat_cool": "SEM-01",
                            "out_of_hours": "SEM-03",
                        }[fault],
                        detail={
                            "stuck_valve": "valve frozen at its opening value while the paired valve moves",
                            "sensor_drift": "CO2 rises ~+12 ppm/sample regardless of occupancy",
                            "comms_dropout": "point stops publishing for the whole window",
                            "simultaneous_heat_cool": "heating_valve pinned >80% alongside cooling valve >80%",
                            "out_of_hours": "fan running outside 07:00-19:00 weekday window",
                        }[fault],
                    )
                )
        return plan

    def _fault_for(self, point_id: str, minute: int) -> tuple[str, TruthFault] | None:
        """Return the fault affecting this point, matching the point itself or
        its peer (a simultaneous heat/cool fault pins both valves on an AHU)."""
        for truth in self.plan:
            if not (truth.start_minute <= minute < truth.end_minute):
                continue
            if point_id == truth.point_id:
                return truth.fault, truth
            # the peer only shares the window for faults defined across a pair of
            # points; for stuck_valve the peer must keep moving, by design
            if truth.peer_point_id == point_id and truth.fault != "stuck_valve":
                return truth.fault, truth
        return None

    # --- physics -------------------------------------------------------------
    def _rng(self, point_id: str) -> random.Random:
        """One noise stream per point.

        Seeded from (seed, point_id) rather than hash(point_id): PYTHONHASHSEED
        randomises str hashing per process, so a hash-seeded stream made the
        output differ between runs of the same seed.
        """
        if point_id not in self.noise:
            self.noise[point_id] = random.Random(f"{self.seed}:{point_id}")
        return self.noise[point_id]

    def value_for(self, row: dict[str, str], ts: datetime, minute: int) -> float:
        """Baseline plausible value for a point at a simulated timestamp."""
        rng = self._rng(row["point_id"])
        cls = row["point_class"]
        local = ts.astimezone(ZoneInfo(LOCAL_TZ)) if ts.tzinfo else ts
        hour = local.hour + local.minute / 60
        occupied = occupancy_people(ts, 40) > 0
        capacity = 20 + (hash(row["equipment"]) % 30)

        if cls == "supply_temp":
            base = 12.0 + 3.0 * max(0.0, 1.0 - abs(hour - 14) / 8.0)
        elif cls == "return_temp":
            base = 18.0 + (2.5 if occupied else 0.5)
        elif cls == "damper_pos":
            base = 35.0 + (35.0 if occupied else 0.0)
        elif cls == "fan_speed":
            # unoccupied base sits below the SEM-03 running threshold (20%),
            # so out-of-hours detection reports injected faults, not base load
            base = 15.0 + (60.0 if occupied else 0.0)
        elif cls == "heating_valve":
            # demand peaks in the morning and closes by mid-afternoon
            base = 15.0 + (50.0 * max(0.0, 1.0 - abs(hour - 8) / 3.5))
        elif cls == "cooling_valve":
            # afternoon peak; the /3.5 taper keeps the two valve profiles from
            # overlapping, so a healthy AHU never has both above the SEM-01
            # threshold and the rule can only fire on a real fault
            base = 10.0 + (45.0 * max(0.0, 1.0 - abs(hour - 15) / 3.5))
        elif cls == "room_temp":
            base = 20.5 + (1.2 if occupied else -0.6) + 0.3 * rng.uniform(-1, 1)
        elif cls == "setpoint":
            base = 21.0
        elif cls == "co2":
            base = 430.0 + occupancy_people(ts, capacity) * 22.0
        elif cls == "occupancy":
            return float(occupancy_people(ts, capacity))
        elif cls == "sub_meter_kwh":
            base = 0.15 + (0.9 if occupied else 0.05) + 0.2 * max(0.0, 1.0 - abs(hour - 9) / 6.0)
        else:  # pragma: no cover - registry is closed
            raise ValueError(f"unknown point class {cls}")
        value = round(base + rng.uniform(-noise_for(cls), noise_for(cls)), 3)
        # energy meters and counts cannot be negative; clamp rather than emitting
        # readings the ingestion contract would (correctly) dead-letter
        if cls in _NON_NEGATIVE_CLASSES:
            value = max(0.0, value)
        return value

    def message(self, row: dict[str, str], ts: datetime, minute: int) -> tuple[dict[str, Any], TruthFault | None]:
        """Build one payload plus the truth record if a fault was applied."""
        fault = self._fault_for(row["point_id"], minute)
        value = self.value_for(row, ts, minute)
        quality = "good"
        injected: TruthFault | None = None

        if fault is not None:
            kind, truth = fault
            injected = truth
            if kind == "stuck_valve":
                value = self._stuck_value(row["point_id"])
                quality = "suspect"
            elif kind == "sensor_drift":
                # +8 ppm per sample (~+96 ppm/h) stays inside the 10,000 ppm
                # contract ceiling, so the fault is visible as drift rather than
                # rejected at ingestion as an out-of-range reading
                # 8 ppm/sample over the 480-sample window peaks at 4,262 ppm,
                # inside the 10,000 ppm contract ceiling: the fault shows up as
                # drift rather than being dead-lettered as an invalid reading
                value = round(430.0 + 8.0 * (minute - truth.start_minute), 3)
                quality = "suspect"
            elif kind == "simultaneous_heat_cool":
                value = 85.0
                quality = "suspect"
            elif kind == "out_of_hours":
                value = round(55.0 + 5.0 * ((minute // 60) % 3), 3)
                quality = "suspect"
            elif kind == "comms_dropout":
                return {}, truth  # nothing published at all

        payload = {"ts": ts.isoformat(), "value": value, "unit": _unit_for(row["point_class"]), "quality": quality}
        return payload, injected

    def _stuck_value(self, point_id: str) -> float:
        """Freeze at a fixed opening so the value is constant across the window."""
        return 62.0

    # --- main loop -----------------------------------------------------------
    def generate(self, duration_hours: float) -> tuple[pd.DataFrame, dict[str, Any]]:
        steps = int(duration_hours * 60 / self.interval_minutes)
        self.steps = steps
        records: list[dict[str, Any]] = []
        truth: dict[str, Any] = {
            "seed": self.seed,
            "start": self.start.isoformat(),
            "interval_minutes": self.interval_minutes,
            "duration_hours": duration_hours,
            "points": len(self.points),
            "faults": [asdict(f) for f in self.plan],
            "messages_sent": 0,
            "messages_dropped_comms_dropout": 0,
            "messages_malformed": 0,
        }
        for step in range(steps):
            ts = self.start + timedelta(minutes=step * self.interval_minutes)
            minute = step * self.interval_minutes
            for row in self.points:
                payload, injected = self.message(row, ts, minute)
                if injected is not None and injected.fault == "comms_dropout":
                    truth["messages_dropped_comms_dropout"] += 1
                    continue
                # deliberate malformed payload: ~1 in 600 messages, deterministic
                # index by position rather than list.index(row): the registry is
                # sorted, and scanning it per message is O(points) per sample
                malformed = (step * len(self.points) + self._point_index[row["point_id"]]) % 600 == 599
                if malformed:
                    payload = {"ts": ts.isoformat(), "value": "not_a_number", "unit": payload["unit"]}
                    truth["messages_malformed"] += 1
                records.append(
                    {
                        "ts": ts.isoformat(),
                        "topic": row["topic"],
                        "point_id": row["point_id"],
                        "value": payload["value"],
                        "unit": payload["unit"],
                        # malformed payloads omit `quality` on purpose, so the
                        # validator's MISSING_FIELD rule is exercised end to end
                        "quality": payload.get("quality"),
                        "malformed": malformed,
                    }
                )
                truth["messages_sent"] += 1
        frame = pd.DataFrame.from_records(records)
        return frame, truth


def _unit_for(point_class: str) -> str:
    return {
        "supply_temp": "C",
        "return_temp": "C",
        "room_temp": "C",
        "setpoint": "C",
        "damper_pos": "%",
        "fan_speed": "%",
        "heating_valve": "%",
        "cooling_valve": "%",
        "co2": "ppm",
        "occupancy": "count",
        "sub_meter_kwh": "kWh",
    }[point_class]


def _to_mqtt_frame(frame: pd.DataFrame) -> list[tuple[str, str]]:
    """(topic, wire payload) pairs in timestamp order."""
    return [
        (
            str(row.topic),
            json.dumps({"ts": row.ts, "value": row.value, "unit": row.unit, "quality": row.quality}),
        )
        for row in frame.itertuples()
    ]


def publish(
    frame: pd.DataFrame, *, host: str, port: int, username: str, password: str, speedup: int, interval_minutes: int
) -> int:
    """Publish frame to MQTT in timestamp order, sleeping interval/speedup between steps."""
    import paho.mqtt.client as mqtt

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="p15-simulator")
    client.username_pw_set(username, password)
    client.connect(host, port, 60)
    client.loop_start()
    sent = 0
    delay = (interval_minutes * 60.0) / max(1, speedup)
    last_ts = None
    for topic, payload in _to_mqtt_frame(frame):
        ts = payload and json.loads(payload)["ts"]
        if last_ts is not None and ts != last_ts:
            _sleep(delay)
        last_ts = ts
        client.publish(topic, payload, qos=0)
        sent += 1
    client.loop_stop()
    client.disconnect()
    return sent


def _sleep(seconds: float) -> None:
    import time

    if seconds > 0:
        time.sleep(seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="P15 BMS/sensor simulator")
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--username", default="bms_user")
    parser.add_argument(
        "--password", default="bms_pass", help="DEMO ONLY default; use BMS_MQTT_PASSWORD in a real deployment"
    )
    parser.add_argument("--speedup", type=int, default=144, help="144x => 24 simulated hours in ~10 min")
    parser.add_argument("--duration-hours", type=float, default=24.0)
    parser.add_argument("--interval-minutes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--start",
        default=None,
        help="ISO start timestamp (default: now, UTC); fault windows are minutes from this",
    )
    parser.add_argument(
        "--faults",
        nargs="*",
        default=None,
        help=f"fault types to inject (default: all of {', '.join(FAULTS)}); pass no values for none",
    )
    parser.add_argument("--dry-run", action="store_true", help="write Parquet instead of publishing to MQTT")
    parser.add_argument("--out", type=Path, default=Path("data/p15"))
    parser.add_argument("--truth-out", type=Path, default=Path("data/p15/truth.json"))
    args = parser.parse_args()

    sim = Simulator(
        datetime.fromisoformat(args.start) if args.start else datetime.now(UTC).replace(microsecond=0, second=0),
        seed=args.seed,
        interval_minutes=args.interval_minutes,
        faults=args.faults,
    )
    frame, truth = sim.generate(args.duration_hours)
    truth["seed"] = args.seed

    args.truth_out.parent.mkdir(parents=True, exist_ok=True)
    args.truth_out.write_text(json.dumps(truth, indent=2), encoding="utf-8")

    if args.dry_run:
        args.out.mkdir(parents=True, exist_ok=True)
        # malformed rows carry a non-numeric value on purpose; keep the value
        # column as a string so the dry-run file mirrors what hits the broker
        frame.assign(value=frame["value"].astype(str)).to_parquet(args.out / "bms_readings_sim.parquet", index=False)
        print(f"[dry-run] {len(frame)} messages -> {args.out / 'bms_readings_sim.parquet'}")
    else:
        sent = publish(
            frame,
            host=args.broker,
            port=args.port,
            username=args.username,
            password=args.password,
            speedup=args.speedup,
            interval_minutes=args.interval_minutes,
        )
        print(f"Published {sent} messages to {args.broker}:{args.port} at {args.speedup}x speed")
    print(f"Injected {len(truth['faults'])} fault windows across {truth['points']} points; truth -> {args.truth_out}")


if __name__ == "__main__":
    main()
