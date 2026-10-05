"""Hand-checked fixtures for P09 compliance status logic."""

import sys
from pathlib import Path
from datetime import date

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compliance import (  # noqa: E402
    AS_OF,
    Status,
    days_overdue,
    overdue_band,
    remedial_ageing,
    risk_score,
    status_for,
)


def test_due_today_is_overdue() -> None:
    # due today -> overdue (0 days overdue but <= as_of)
    s = status_for(due_date=AS_OF, completed_date=None, result=None, has_open_remedial=False, as_of=AS_OF)
    assert s == Status.OVERDUE
    assert days_overdue(AS_OF, AS_OF) == 0


def test_due_in_30_days_is_due_soon() -> None:
    # due in exactly 30 days
    due = date.fromordinal(AS_OF.toordinal() + 30)
    s = status_for(due_date=due, completed_date=None, result=None, has_open_remedial=False, as_of=AS_OF)
    assert s == Status.DUE_SOON


def test_due_in_31_days_is_compliant() -> None:
    due = date.fromordinal(AS_OF.toordinal() + 31)
    s = status_for(due_date=due, completed_date=None, result=None, has_open_remedial=False, as_of=AS_OF)
    assert s == Status.COMPLIANT


def test_completed_on_due_date_is_compliant() -> None:
    s = status_for(due_date=AS_OF, completed_date=AS_OF, result="Pass", has_open_remedial=False, as_of=AS_OF)
    assert s == Status.COMPLIANT


def test_completed_after_due_date_is_overdue() -> None:
    s = status_for(due_date=date(2026, 3, 1), completed_date=date(2026, 3, 10), result="Pass", has_open_remedial=False, as_of=AS_OF)
    assert s == Status.OVERDUE


def test_failed_with_open_remedial_is_failed_remedial_open() -> None:
    s = status_for(due_date=date(2025, 12, 1), completed_date=None, result="Fail", has_open_remedial=True, as_of=AS_OF)
    assert s == Status.FAILED_REMEDIAL_OPEN


def test_completed_late_is_overdue_not_compliant() -> None:
    # completed after due date = overdue (completed late)
    s = status_for(due_date=date(2025, 12, 1), completed_date=date(2026, 2, 1), result="Pass", has_open_remedial=False, as_of=AS_OF)
    assert s == Status.OVERDUE


def test_no_record_when_no_due_no_completed() -> None:
    s = status_for(due_date=None, completed_date=None, result=None, has_open_remedial=False, as_of=AS_OF)
    assert s == Status.NO_RECORD


def test_overdue_bands() -> None:
    assert overdue_band(None) == 0
    assert overdue_band(0) == 0
    assert overdue_band(1) == 1
    assert overdue_band(30) == 1
    assert overdue_band(31) == 2
    assert overdue_band(90) == 2
    assert overdue_band(91) == 3
    assert overdue_band(180) == 3
    assert overdue_band(181) == 4
    assert overdue_band(365) == 4


def test_risk_score() -> None:
    # criticality 5, 45 days over (band 2), Fail -> 5*2*2 = 20
    assert risk_score(5, 45, "Fail") == 20
    # criticality 3, 10 days over (band 1), Pass -> 3*1*1 = 3
    assert risk_score(3, 10, "Pass") == 3
    # no overdue -> 0
    assert risk_score(5, 0, "Fail") == 0
    assert risk_score(5, None, "Fail") == 0


def test_remedial_ageing() -> None:
    opened = date(2026, 1, 1)
    closed = date(2026, 3, 1)
    # When closed: age at closure date
    assert remedial_ageing(opened, closed, AS_OF) == 59
    # When still open: age as of AS_OF
    assert remedial_ageing(opened, None, AS_OF) == 89
    assert remedial_ageing(None, None, AS_OF) is None