"""P15 ingestion validation contract (Python side).

Mirrors the rules in `contracts/validation_rules.json` that the Node-RED flow
enforces at runtime. Tests assert this module and the JSON contract stay in
sync, so the Python tests exercise the same rules the running pipeline uses.

Usage:
    validate = Validator.from_repo(Path("projects/p15-bms-iot"))
    result = validate.check("campus/B003/ahu/supply_temp", payload_bytes, now=...)
    if result.ok: ...
    else: -> bms.dead_letter with result.reason
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]

# reason codes written to bms.dead_letter.reason
R_TOPIC = "TOPIC_PATTERN"
R_JSON = "MALFORMED_JSON"
R_SCHEMA = "MISSING_FIELD"
R_VALUE = "NON_NUMERIC_VALUE"
R_UNIT = "UNIT_MISMATCH"
R_RANGE = "OUT_OF_RANGE"
R_TS_FUTURE = "TIMESTAMP_IN_FUTURE"
R_TS_OLD = "TIMESTAMP_TOO_OLD"
R_TS_FORMAT = "TIMESTAMP_FORMAT"
R_QUALITY = "QUALITY_INVALID"
R_UNKNOWN_POINT = "UNKNOWN_POINT_ID"


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    reason: str | None = None
    point_id: str | None = None
    ts: datetime | None = None
    value: float | None = None
    unit: str | None = None
    quality: str | None = None


# unit aliases -> canonical unit; F is converted, not just relabelled
_UNIT_ALIASES: dict[str, str] = {
    "c": "C",
    "degc": "C",
    "°c": "C",
    "celsius": "C",
    "f": "F",
    "degf": "F",
    "°f": "F",
    "fahrenheit": "F",
    "%": "%",
    "pct": "%",
    "percent": "%",
    "ppm": "ppm",
    "count": "count",
    "kwh": "kWh",
    "kwh/h": "kWh",
}


def normalise_unit(unit: str) -> str:
    """Map a unit string to its canonical form (case/alias insensitive)."""
    return _UNIT_ALIASES.get(unit.strip().lower(), unit.strip())


def to_celsius(value: float, unit: str) -> float:
    """Convert F to C; other canonical units pass through unchanged."""
    if normalise_unit(unit) == "F":
        return (value - 32.0) * 5.0 / 9.0
    return value


class Validator:
    """Validates MQTT payloads against the shared contract."""

    def __init__(self, rules: dict[str, Any], registry: dict[str, dict[str, str]]) -> None:
        self.rules = rules
        self.registry = registry
        self.topic_re = re.compile(rules["topic_pattern"])
        self._by_topic = {row["topic"]: point_id for point_id, row in registry.items()}

    @classmethod
    def from_repo(cls, root: Path = REPO, registry_csv: Path | None = None) -> Validator:
        rules = json.loads((root / "contracts" / "validation_rules.json").read_text(encoding="utf-8"))
        return cls(rules, load_registry(registry_csv or root / "src" / "point_registry.csv"))

    # --- topic ---------------------------------------------------------------
    def parse_topic(self, topic: str) -> tuple[str, str, str, str] | None:
        """Return (building, system, equipment, point_class), or None if malformed."""
        match = self.topic_re.match(topic)
        if match is None:
            return None
        return (
            match.group("building"),
            match.group("system"),
            match.group("equipment"),
            match.group("point_class"),
        )

    def point_id_for_topic(self, topic: str) -> str | None:
        return self._by_topic.get(topic)

    # --- payload -------------------------------------------------------------
    def check(self, topic: str, payload: str | bytes, *, now: datetime | None = None) -> CheckResult:
        """Validate one MQTT message. Returns a CheckResult; never raises."""
        now = now or datetime.now(UTC)
        parsed = self.parse_topic(topic)
        if parsed is None:
            return CheckResult(ok=False, reason=R_TOPIC)
        _, _, _, point_class = parsed

        if isinstance(payload, bytes):
            try:
                payload = payload.decode("utf-8")
            except UnicodeDecodeError:
                return CheckResult(ok=False, reason=R_JSON)
        try:
            body = json.loads(payload)
        except json.JSONDecodeError:
            return CheckResult(ok=False, reason=R_JSON)
        if not isinstance(body, dict):
            return CheckResult(ok=False, reason=R_SCHEMA)

        for field in self.rules["payload_schema"]["required_fields"]:
            if field not in body:
                return CheckResult(ok=False, reason=R_SCHEMA)

        quality = str(body["quality"])
        if quality not in self.rules["payload_schema"]["allowed_quality"]:
            return CheckResult(ok=False, reason=R_QUALITY, quality=quality)

        raw_value = body["value"]
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            return CheckResult(ok=False, reason=R_VALUE, quality=quality)
        value = float(raw_value)
        if abs(value) > self.rules["max_value_abs"]:
            return CheckResult(ok=False, reason=R_RANGE, value=value, quality=quality)

        ts = _parse_ts(body["ts"])
        if ts is None:
            return CheckResult(ok=False, reason=R_TS_FORMAT, quality=quality)
        if ts > now + timedelta(minutes=self.rules["max_future_skew_minutes"]):
            return CheckResult(ok=False, reason=R_TS_FUTURE, ts=ts, quality=quality)
        if ts < now - timedelta(hours=self.rules["max_past_age_hours"]):
            return CheckResult(ok=False, reason=R_TS_OLD, ts=ts, quality=quality)

        class_rule = self.rules["rules_by_point_class"].get(point_class)
        if class_rule is None:
            return CheckResult(ok=False, reason=R_SCHEMA, ts=ts, quality=quality)

        sent_unit = normalise_unit(str(body["unit"]))
        # a temperature sent in Fahrenheit is converted, not rejected: the point
        # stores Celsius either way, and refusing it would lose the reading
        # rather than fix the controller's configuration
        if sent_unit != class_rule["unit"]:
            convertible = {class_rule["unit"], "F"} if class_rule["unit"] == "C" else {class_rule["unit"]}
            if sent_unit not in convertible:
                return CheckResult(ok=False, reason=R_UNIT, ts=ts, unit=sent_unit, quality=quality)
        value = to_celsius(value, sent_unit)
        if not (class_rule["min"] <= value <= class_rule["max"]):
            return CheckResult(ok=False, reason=R_RANGE, ts=ts, value=value, unit=sent_unit, quality=quality)

        point_id = self.point_id_for_topic(topic)
        if point_id is None:
            return CheckResult(ok=False, reason=R_UNKNOWN_POINT, ts=ts, value=value, unit=sent_unit, quality=quality)

        return CheckResult(ok=True, point_id=point_id, ts=ts, value=value, unit=sent_unit, quality=quality)


def _parse_ts(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    text = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


@lru_cache(maxsize=4)
def load_registry(path: str) -> dict[str, dict[str, str]]:
    """Load the point registry CSV into {point_id: row}."""
    import csv

    with Path(path).open(encoding="utf-8") as fh:
        return {row["point_id"]: row for row in csv.DictReader(fh)}
