"""P17 configuration (YAML + env overrides)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Data paths
    truth_dir: Path = Field(default=Path("data/truth"), description="Foundation truth parquet dir")
    output_dir: Path = Field(default=Path("data/p17_output"), description="Output directory")

    # Ventilation thresholds (ppm) — sources cited in docs/methodology.md
    co2_threshold_low_ppm: int = 1000
    co2_threshold_high_ppm: int = 1500

    # Thermal comfort band (°C)
    comfort_temp_min_c: float = 18.0
    comfort_temp_max_c: float = 24.0
    overheating_threshold_c: float = 26.0

    # Occupancy analysis
    no_show_threshold_min: int = 10  # session start delay to count as no-show
    overcapacity_tolerance: float = 1.0  # allow 100% capacity

    # Sensor health
    stuck_value_window: int = 12  # 15-min periods (3 hours)
    dropout_max_gap_periods: int = 4  # max 1 hour gap
    drift_window_days: int = 14
    drift_percentile: float = 0.01  # 1st percentile for drift detection

    # Room archetypes
    archetype_n_clusters: int = 5
    archetype_random_state: int = 42

    # Out-of-hours (building local time, UTC-aware in data)
    occupied_start_hour: int = 8
    occupied_end_hour: int = 18
    weekend_occupied: bool = False

    # Output formats
    write_parquet: bool = True
    write_csv: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()