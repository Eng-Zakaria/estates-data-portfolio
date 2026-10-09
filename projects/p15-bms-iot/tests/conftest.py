"""Shared fixtures for the P15 tests.

Tests import the modules from `src/` by path (the project is not installed as a
package) and work on small hand-built frames, so every assertion is about a
number someone can check by eye.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REGISTRY_CSV = SRC / "point_registry.csv"
CONTRACT = PROJECT / "contracts" / "validation_rules.json"
FLOW_MERGED = PROJECT / "flows" / "p15_bms.json"

# A Wednesday, so weekday rules (SEM-03) are exercised and the 24 h window
# covers a full teaching day. Local midnight in UTC terms is 23:00 the day
# before during BST, which is what the simulator expects.
START = datetime(2026, 10, 7, 23, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def project() -> Path:
    return PROJECT


@pytest.fixture(scope="session")
def rules() -> dict:
    import json

    return json.loads(CONTRACT.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def registry() -> dict[str, dict[str, str]]:
    from validate import load_registry

    return load_registry(str(REGISTRY_CSV))


@pytest.fixture(scope="session")
def validator():
    from validate import Validator

    return Validator.from_repo(PROJECT)


@pytest.fixture
def sim():
    """A short simulator: 6 h at a 5-min cadence covers every fault class."""
    from simulator import Simulator

    return Simulator(START, seed=7, interval_minutes=5)


def readings_from(frame: pd.DataFrame) -> pd.DataFrame:
    """Shape a raw simulator frame like the pipeline sees it."""
    return frame[["ts", "topic", "value", "unit", "quality"]].copy()


def payload(
    *,
    ts: datetime = START,
    value: object = 21.0,
    unit: str = "C",
    quality: str = "good",
    drop: tuple[str, ...] = (),
) -> str:
    """A valid wire payload, with fields removed for negative tests."""
    import json

    stamp = ts if isinstance(ts, str) else ts.isoformat()
    body: dict[str, object] = {"ts": stamp, "value": value, "unit": unit, "quality": quality}
    for field in drop:
        body.pop(field, None)
    return json.dumps(body)