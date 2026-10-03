"""Shared fixtures: generate small truth once per session (fast)."""

from __future__ import annotations

import pytest
from campus_synth.config import get_profile
from campus_synth.generator import generate_all


@pytest.fixture(scope="session")
def small_profile():
    return get_profile("small", seed=42, defects=0.03)


@pytest.fixture(scope="session")
def small_truth(small_profile):
    tables, gt = generate_all(small_profile)
    return tables, gt
