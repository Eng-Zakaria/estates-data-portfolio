"""Net-zero carbon calculations (P08) — pure functions over gold-mart grains.

All data synthetic. Fuel factors come from the DESNZ 2025 seed (see DATA.md),
never hard-coded here: callers pass the factor in.
"""

from __future__ import annotations

# Utility (meter grain) -> (carbon fuel key, GHG Protocol scope).
FUEL_SCOPE: dict[str, tuple[str, str]] = {
    "electricity": ("electricity", "Scope 2"),
    "gas": ("natural_gas", "Scope 1"),
}


def kwh_to_kgco2e(kwh: float, factor_kgco2e_per_kwh: float) -> float:
    """Convert energy to emissions. Factor is an argument, never a constant."""
    return kwh * factor_kgco2e_per_kwh


def intensity(value: float, gia_m2: float | None) -> float | None:
    """kWh/m2 or kgCO2e/m2. None when floor area is missing/non-positive."""
    if gia_m2 is None or gia_m2 <= 0:
        return None
    return value / gia_m2


def normalise_gas_hdd(kwh: float, hdd: float, ref_hdd: float) -> float | None:
    """Degree-day ratio normalisation: what gas use would be in a `ref_hdd` period.

    Assumes heating load scales linearly with HDD and ignores baseload split —
    see methodology.md for limits. None when hdd is zero/missing.
    """
    if hdd is None or hdd <= 0 or ref_hdd is None or ref_hdd <= 0:
        return None
    return kwh * ref_hdd / hdd


def linear_pathway(baseline_annual: float, base_year: int, target_year: int, year: int) -> float:
    """Straight-line pathway from baseline (base_year) to net zero (target_year)."""
    if target_year <= base_year:
        raise ValueError("target_year must be after base_year")
    if year <= base_year:
        return baseline_annual
    if year >= target_year:
        return 0.0
    return baseline_annual * (1.0 - (year - base_year) / (target_year - base_year))


def variance_to_pathway(actual: float, pathway: float | None) -> float | None:
    """(actual - pathway) / pathway. None when pathway is missing or zero."""
    if pathway is None or pathway == 0:
        return None
    return (actual - pathway) / pathway


def baseload_pct(overnight_min_kw: float, daily_peak_kw: float | None) -> float | None:
    """Overnight baseload as % of daily peak. None when peak is missing/zero."""
    if daily_peak_kw is None or daily_peak_kw <= 0:
        return None
    return overnight_min_kw / daily_peak_kw * 100.0


def rolling_mean(values: list[float], window: int = 12) -> list[float | None]:
    """Trailing mean over `window` periods (partial windows allowed, noted)."""
    out: list[float | None] = []
    for i in range(len(values)):
        part = values[max(0, i - window + 1) : i + 1]
        out.append(sum(part) / len(part) if part else None)
    return out
