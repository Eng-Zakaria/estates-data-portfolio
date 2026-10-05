"""Hand-checked fixtures for P08 carbon calculations (all values by hand)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carbon import (  # noqa: E402
    FUEL_SCOPE,
    baseload_pct,
    intensity,
    kwh_to_kgco2e,
    linear_pathway,
    normalise_gas_hdd,
    rolling_mean,
    variance_to_pathway,
)


def test_scope_map() -> None:
    assert FUEL_SCOPE["electricity"] == ("electricity", "Scope 2")
    assert FUEL_SCOPE["gas"] == ("natural_gas", "Scope 1")


def test_one_meter_one_month() -> None:
    # Acceptance fixture: 1 meter, Jan, 100 kWh electricity @ 0.177 -> 17.7 kgCO2e.
    assert kwh_to_kgco2e(100.0, 0.177) == pytest.approx(17.7)
    assert kwh_to_kgco2e(200.0, 0.2027) == pytest.approx(40.54)


def test_intensity() -> None:
    assert intensity(900.0, 1500.0) == pytest.approx(0.6)
    assert intensity(900.0, 0.0) is None
    assert intensity(900.0, None) is None


def test_hdd_normalisation() -> None:
    # 1000 kWh at 200 HDD scales to 1250 kWh at reference 250 HDD.
    assert normalise_gas_hdd(1000.0, 200.0, 250.0) == pytest.approx(1250.0)
    assert normalise_gas_hdd(1000.0, 0.0, 250.0) is None


def test_pathway_and_variance() -> None:
    # Baseline 1000 in 2024, net zero 2040 -> 2026 pathway = 1000*(1-2/16) = 875.
    assert linear_pathway(1000.0, 2024, 2040, 2026) == pytest.approx(875.0)
    assert linear_pathway(1000.0, 2024, 2040, 2040) == pytest.approx(0.0)
    assert linear_pathway(1000.0, 2024, 2040, 2023) == pytest.approx(1000.0)
    # Actual 900 vs pathway 875 -> +2.857%.
    assert variance_to_pathway(900.0, 875.0) == pytest.approx(0.028571, rel=1e-4)
    assert variance_to_pathway(900.0, None) is None
    assert variance_to_pathway(900.0, 0.0) is None
    with pytest.raises(ValueError):
        linear_pathway(1000.0, 2040, 2040, 2030)


def test_baseload_pct() -> None:
    # Overnight min 8 kW vs daily peak 50 kW -> 16%.
    assert baseload_pct(8.0, 50.0) == pytest.approx(16.0)
    assert baseload_pct(8.0, 0.0) is None
    assert baseload_pct(8.0, None) is None


def test_rolling_mean() -> None:
    assert rolling_mean([10.0, 20.0, 30.0], window=12) == pytest.approx([10.0, 15.0, 20.0])
    assert rolling_mean([10.0, 20.0, 30.0, 40.0], window=2) == pytest.approx([10.0, 15.0, 25.0, 35.0])
    assert rolling_mean([]) == []
