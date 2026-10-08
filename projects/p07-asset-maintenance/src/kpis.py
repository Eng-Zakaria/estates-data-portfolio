"""Asset & maintenance KPIs (P07) - pure functions.

All data synthetic. SLA targets and bands live with the config/methodology:
see methodology.md. Nothing here reads files or databases.
"""

from __future__ import annotations

from datetime import date, datetime

# Illustrative SLA targets in days by priority (config, not from data).
SLA_TARGET_DAYS: dict[str, float] = {"P1": 1.0, "P2": 5.0, "P3": 10.0, "P4": 20.0}


def ppm_completion(complete: int, raised: int) -> float | None:
    """PPM jobs completed / PPM jobs raised. None when none raised."""
    if raised is None or raised <= 0:
        return None
    return complete / raised


def planned_reactive_ratio(planned: int, reactive: int) -> float | None:
    """Planned + statutory + project / reactive. None when no reactive."""
    if reactive is None or reactive <= 0:
        return None
    return planned / reactive


def age_band(age_days: float | None) -> str | None:
    """Backlog age banding: 0-30 / 31-90 / 91-180 / 180+ / unknown."""
    if age_days is None or age_days < 0:
        return None
    if age_days <= 30:
        return "0-30"
    if age_days <= 90:
        return "31-90"
    if age_days <= 180:
        return "91-180"
    return "180+"


def sla_met(days_to_complete: float | None, target_days: float | None) -> bool | None:
    """True when the job finished within its SLA. None when not computable."""
    if days_to_complete is None or target_days is None or target_days <= 0:
        return None
    return days_to_complete <= target_days


def mttr(days_to_complete: list[float]) -> float | None:
    """Mean time to repair (reactive jobs). None when no completions."""
    vals = [d for d in days_to_complete if d is not None and d >= 0]
    if not vals:
        return None
    return sum(vals) / len(vals)


def mtbf(failure_days: list[float]) -> float | None:
    """Mean time between failures from sorted failure day-numbers.

    Only meaningful for assets with >= 2 failures; None otherwise.
    """
    days = sorted(d for d in failure_days if d is not None)
    if len(days) < 2:
        return None
    gaps = [b - a for a, b in zip(days, days[1:])]
    return sum(gaps) / len(gaps)


def is_repeat_failure(reactive_count_12m: int, threshold: int = 3) -> bool:
    """Repeat-failure asset: >= threshold reactive jobs in 12 months."""
    return reactive_count_12m >= threshold


def remaining_life_pct(age_years: float | None, expected_life_years: float | None) -> float | None:
    """Remaining life % = 1 - age/expected. None when missing or non-positive.

    Can be negative (over-life assets) - reported as-is, clamped only for
    display in Power BI if needed.
    """
    if age_years is None or expected_life_years is None or expected_life_years <= 0:
        return None
    return 1.0 - age_years / expected_life_years


def renewal_year(install: date | datetime | None, expected_life_years: float | None) -> int | None:
    """Expected replacement year = install year + expected life."""
    if install is None or expected_life_years is None:
        return None
    if isinstance(install, datetime):
        install = install.date()
    return install.year + int(expected_life_years)


def renewal_forecast(pairs: list[tuple[int | None, float]], years: range) -> dict[int, float]:
    """Sum replacement cost by renewal year within `years`.

    `pairs` = (renewal_year, replacement_cost). Drivers with unknown years
    are dropped (reported as a coverage gap, not forecast).
    """
    out = {y: 0.0 for y in years}
    for yr, cost in pairs:
        if yr is not None and yr in out and cost is not None:
            out[yr] += float(cost)
    return out


def cost_per_m2(cost_gbp: float | None, gia_m2: float | None) -> float | None:
    """Cost per m2 GIA. None when area missing/non-positive."""
    if cost_gbp is None or gia_m2 is None or gia_m2 <= 0:
        return None
    return cost_gbp / gia_m2


def risk_band(criticality: int | None, condition_grade: str | None) -> str | None:
    """Criticality x condition matrix: band = criticality x condition weight.

    Condition weight: A=1, B=2, C=3, D=4. Band: >=16 High, >=9 Medium,
    >0 Low, else Unknown.
    """
    if criticality is None or condition_grade is None:
        return None
    weight = {"A": 1, "B": 2, "C": 3, "D": 4}.get(str(condition_grade).strip().upper())
    if weight is None or criticality <= 0:
        return None
    score = criticality * weight
    if score >= 16:
        return "High"
    if score >= 9:
        return "Medium"
    return "Low"
