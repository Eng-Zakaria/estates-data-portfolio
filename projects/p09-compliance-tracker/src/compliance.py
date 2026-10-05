"""Compliance status logic (P09) — pure functions, unit-tested with boundary cases.

All data synthetic. Status logic single source of truth; see methodology.md.
"""

from __future__ import annotations

from datetime import date
from enum import Enum


class Status(str, Enum):
    COMPLIANT = "Compliant"
    DUE_SOON = "Due within 30 days"
    OVERDUE = "Overdue"
    FAILED_REMEDIAL_OPEN = "Failed – remedial open"
    NO_RECORD = "No record"


def status_for(
    *,
    due_date: date | None,
    completed_date: date | None,
    result: str | None,
    has_open_remedial: bool,
    as_of: date,
) -> Status:
    """Single status logic (spec §Data and logic).

    Priority order:
    1. If failed and has open remedial -> FAILED_REMEDIAL_OPEN
    2. If no due_date and no completed_date -> NO_RECORD
    3. If completed_date and completed_date <= due_date -> COMPLIANT
    4. If completed_date and completed_date > due_date -> OVERDUE
    5. If due_date <= as_of -> OVERDUE
    6. If due_date <= as_of + 30 days -> DUE_SOON
    7. -> COMPLIANT
    """
    # 1. Failed with open remedial
    if result == "Fail" and has_open_remedial:
        return Status.FAILED_REMEDIAL_OPEN

    # 2. No record at all
    if due_date is None and completed_date is None:
        return Status.NO_RECORD

    # 3–6. Has a due date
    if due_date is not None:
        if completed_date is not None:
            if completed_date <= due_date:
                return Status.COMPLIANT
            else:
                return Status.OVERDUE
        else:
            if due_date <= as_of:
                return Status.OVERDUE
            elif due_date <= date.fromordinal(as_of.toordinal() + 30):
                return Status.DUE_SOON
            else:
                return Status.COMPLIANT

    # Fallback (completed but no due — treat as compliant)
    return Status.COMPLIANT


def days_overdue(due_date: date | None, as_of: date) -> int | None:
    """Days past due (positive when overdue). None when no due date."""
    if due_date is None:
        return None
    delta = (as_of - due_date).days
    return delta if delta > 0 else 0


def overdue_band(days_over: int | None) -> int:
    """Map days overdue to band weight (1–4)."""
    if days_over is None or days_over <= 0:
        return 0
    if days_over <= 30:
        return 1
    if days_over <= 90:
        return 2
    if days_over <= 180:
        return 3
    return 4


def risk_score(criticality: int, days_over: int | None, result: str | None) -> int:
    """risk = criticality (1–5) × overdue_band (1–4) × failure_flag (1 or 2).

    failure_flag = 2 if result == "Fail" else 1.
    """
    failure_flag = 2 if result == "Fail" else 1
    return criticality * overdue_band(days_over) * failure_flag


def remedial_ageing(
    remedial_opened: date | None,
    remedial_closed: date | None,
    as_of: date,
) -> int | None:
    """Days since remedial opened (if still open). None when closed or no date."""
    if remedial_opened is None:
        return None
    end = remedial_closed if remedial_closed is not None else as_of
    return (end - remedial_opened).days


# --- Boundary test constants (for golden fixtures) ---
# as_of = 2026-03-31 (end of synthetic window)
AS_OF = date(2026, 3, 31)