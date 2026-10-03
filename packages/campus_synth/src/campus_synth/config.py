"""Shared version + profile configuration."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"

ProfileName = Literal["small", "default"]


class ProfileConfig(BaseModel):
    """Deterministic sizing per profile. Counts are targets (spaces/assets exact-ish)."""

    name: ProfileName = "small"
    seed: int = 42
    n_buildings: int = 8
    n_months: int = 3
    end_date: date = Field(default_factory=lambda: date(2026, 3, 31))
    target_spaces: int = 500
    target_assets: int = 1500
    target_work_orders: int = 6000
    n_sensor_rooms: int = 30
    defects: float = 0.03

    model_config = {"frozen": True}


PROFILES: dict[str, ProfileConfig] = {
    "small": ProfileConfig(
        name="small",
        n_buildings=8,
        n_months=3,
        target_spaces=500,
        target_assets=1500,
        target_work_orders=6000,
        n_sensor_rooms=30,
    ),
    "default": ProfileConfig(
        name="default",
        n_buildings=40,
        n_months=24,
        target_spaces=3000,
        target_assets=12000,
        target_work_orders=60000,
        n_sensor_rooms=150,
    ),
}


def get_profile(name: str, seed: int = 42, defects: float = 0.03) -> ProfileConfig:
    """Return a copy of the named profile with seed/defects overridden."""
    if name not in PROFILES:
        raise ValueError(f"unknown profile {name!r}; choose from {sorted(PROFILES)}")
    if not 0.0 <= defects <= 1.0:
        raise ValueError("--defects must be in 0.0..1.0")
    base = PROFILES[name].model_dump()
    base.update(seed=seed, defects=defects)
    return ProfileConfig(**base)
