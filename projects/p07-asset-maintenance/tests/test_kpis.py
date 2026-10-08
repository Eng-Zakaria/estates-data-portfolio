"""Hand-checked fixtures for P07 maintenance KPIs (acceptance: MTTR,
backlog age banding, renewal forecast)."""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpis import (  # noqa: E402
    age_band,
    cost_per_m2,
    is_repeat_failure,
    mtbf,
    mttr,
    planned_reactive_ratio,
    ppm_completion,
    remaining_life_pct,
    renewal_forecast,
    renewal_year,
    risk_band,
    sla_met,
)


def test_mttr_fixture() -> None:
    # 3 reactive jobs completed in 2, 4, 6 days -> MTTR = 4 days.
    assert mttr([2.0, 4.0, 6.0]) == pytest.approx(4.0)
    assert mttr([]) is None
    assert mttr([None]) is None  # type: ignore[list-item]


def test_backlog_age_bands() -> None:
    # Boundary table: 0 and 30 -> 0-30; 31 and 90 -> 31-90;
    # 91 and 180 -> 91-180; 181 -> 180+; negative/unknown -> None.
    assert age_band(0) == "0-30"
    assert age_band(30) == "0-30"
    assert age_band(31) == "31-90"
    assert age_band(90) == "31-90"
    assert age_band(91) == "91-180"
    assert age_band(180) == "91-180"
    assert age_band(181) == "180+"
    assert age_band(-5) is None
    assert age_band(None) is None


def test_renewal_forecast_fixture() -> None:
    # 3 assets due 2027 (£10k, £5k), 1 due 2029 (£20k), 1 unknown year.
    pairs = [(2027, 10000.0), (2027, 5000.0), (2029, 20000.0), (None, 7000.0)]
    out = renewal_forecast(pairs, range(2026, 2031))
    assert out[2027] == pytest.approx(15000.0)
    assert out[2029] == pytest.approx(20000.0)
    assert out[2026] == 0.0
    # Renewal year derivation: installed 2015, 12-year life -> 2027.
    assert renewal_year(date(2015, 6, 1), 12) == 2027
    assert renewal_year(None, 12) is None


def test_ppm_and_ratio() -> None:
    assert ppm_completion(80, 100) == pytest.approx(0.8)
    assert ppm_completion(0, 0) is None
    assert planned_reactive_ratio(90, 30) == pytest.approx(3.0)
    assert planned_reactive_ratio(90, 0) is None


def test_sla_mtbf_repeat() -> None:
    assert sla_met(1.0, 1.0) is True  # due today counts as met
    assert sla_met(2.0, 1.0) is False
    assert sla_met(None, 1.0) is None
    # Failures on days 10, 40, 70 -> gaps 30, 30 -> MTBF 30.
    assert mtbf([10.0, 40.0, 70.0]) == pytest.approx(30.0)
    assert mtbf([10.0]) is None  # need >= 2 failures
    assert is_repeat_failure(3) is True
    assert is_repeat_failure(2) is False


def test_remaining_life_and_cost() -> None:
    assert remaining_life_pct(5, 20) == pytest.approx(0.75)
    assert remaining_life_pct(25, 20) == pytest.approx(-0.25)  # over life
    assert remaining_life_pct(5, 0) is None
    assert cost_per_m2(1000.0, 250.0) == pytest.approx(4.0)
    assert cost_per_m2(1000.0, 0) is None


def test_risk_band() -> None:
    assert risk_band(5, "D") == "High"  # score 20
    assert risk_band(3, "C") == "Medium"  # score 9
    assert risk_band(1, "A") == "Low"  # score 1
    assert risk_band(None, "A") is None
    assert risk_band(3, "E") is None
