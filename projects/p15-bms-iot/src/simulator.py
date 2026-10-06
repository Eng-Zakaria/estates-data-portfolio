"""P15 BMS/sensor simulator: publishes synthetic BMS readings to MQTT.

~20 plant items (AHUs, boilers, pumps) and ~50 rooms across 3 buildings.
Points: supply/return air temp, damper position, fan speed, heating/cooling valve,
room temp/setpoint, CO2, occupancy, electrical sub-meter kWh.
Topics: campus/<building>/<system>/<point>
Payload: {ts, value, unit, quality}
Fault modes configurable and logged to truth file.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

import paho.mqtt.client as mqtt

BUILDINGS = ["B001", "B003", "B007"]
SYSTEMS = ["ahu", "boiler", "pump", "room"]
POINT_CLASSES = [
    ("supply_temp", "C"),
    ("return_temp", "C"),
    ("damper_pos", "%"),
    ("fan_speed", "%"),
    ("heating_valve", "%"),
    ("cooling_valve", "%"),
    ("room_temp", "C"),
    ("setpoint", "C"),
    ("co2", "ppm"),
    ("occupancy", "count"),
    ("sub_meter_kwh", "kWh"),
]

FAULTS = ["stuck_valve", "sensor_drift", "comms_dropout", "simultaneous_heat_cool", "out_of_hours", "malformed_payload"]


def generate_value(point_class: str, ts: datetime, fault: str | None = None) -> tuple[float, str]:
    """Generate plausible value; apply fault if requested."""
    base = {
        "supply_temp": 12.0 + random.uniform(-2, 2),
        "return_temp": 18.0 + random.uniform(-1, 1),
        "damper_pos": 50.0 + random.uniform(-10, 10),
        "fan_speed": 60.0 + random.uniform(-5, 5),
        "heating_valve": 30.0 + random.uniform(-5, 5),
        "cooling_valve": 10.0 + random.uniform(-3, 3),
        "room_temp": 21.0 + random.uniform(-1, 1),
        "setpoint": 21.0,
        "co2": 600.0 + random.uniform(-100, 200),
        "occupancy": random.randint(0, 30),
        "sub_meter_kwh": 5.0 + random.uniform(-1, 1),
    }
    val = base.get(point_class, 0.0)
    quality = "good"

    if fault == "stuck_valve" and point_class in ("heating_valve", "cooling_valve"):
        val = base[point_class]  # constant
        quality = "suspect"
    elif fault == "sensor_drift" and point_class == "co2":
        val = 600.0 + (ts.hour * 50)  # drifts up through day
        quality = "suspect"
    elif fault == "comms_dropout":
        val = 0.0
        quality = "bad"
    elif fault == "simultaneous_heat_cool" and point_class in ("heating_valve", "cooling_valve"):
        val = 80.0
        quality = "suspect"
    elif fault == "out_of_hours" and point_class in ("fan_speed", "heating_valve"):
        val = 50.0
        quality = "suspect"
    elif fault == "malformed_payload":
        return -999.0, "bad"

    return val, quality


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--speedup", type=int, default=144, help="24h in <=10 min => ~144x")
    parser.add_argument("--duration-hours", type=float, default=24.0)
    parser.add_argument("--faults", nargs="*", default=FAULTS)
    parser.add_argument("--truth-out", type=Path, default=Path("projects/p15-bms-iot/truth_faults.json"))
    args = parser.parse_args()

    client = mqtt.Client()
    client.username_pw_set("bms_user", "bms_pass")  # DEMO ONLY
    client.connect(args.broker, args.port, 60)
    client.loop_start()

    truth = {"faults": [], "messages_sent": 0, "faults_injected": 0}
    start = datetime.utcnow()
    interval = timedelta(minutes=5)

    for step in range(int(args.duration_hours * 60 / 5)):
        ts = start + step * interval
        for bldg in BUILDINGS:
            for system in SYSTEMS:
                for point_class, unit in POINT_CLASSES:
                    # Decide fault
                    fault = random.choice(args.faults) if random.random() < 0.02 else None
                    val, quality = generate_value(point_class, ts, fault)
                    payload = {"ts": ts.isoformat(), "value": val, "unit": unit, "quality": quality}
                    if fault == "malformed_payload":
                        payload = {"ts": ts.isoformat(), "value": "not_a_number", "unit": unit}
                    topic = f"campus/{bldg}/{system}/{point_class}"
                    client.publish(topic, json.dumps(payload))
                    truth["messages_sent"] += 1
                    if fault:
                        truth["faults"].append({"ts": ts.isoformat(), "topic": topic, "fault": fault})
                        truth["faults_injected"] += 1

        # Sleep accelerated
        time.sleep(interval.total_seconds() / args.speedup)

    client.loop_stop()
    client.disconnect()
    args.truth_out.parent.mkdir(parents=True, exist_ok=True)
    args.truth_out.write_text(json.dumps(truth, indent=2))
    print(f"Sent {truth['messages_sent']} messages, injected {truth['faults_injected']} faults")
    print(f"Truth file: {args.truth_out}")


if __name__ == "__main__":
    main()
