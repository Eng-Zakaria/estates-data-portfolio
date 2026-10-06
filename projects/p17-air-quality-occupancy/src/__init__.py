"""P17 Smart Campus air quality and occupancy analytics."""

from .config import Settings, get_settings
from .data import load_sensors, load_readings, load_spaces, load_timetable
from .ventilation import compute_ventilation_metrics, compute_ventilation_risk_score
from .comfort import compute_thermal_comfort, compute_comfort_risk_score
from .occupancy import compute_occupancy_analysis, compute_occupancy_utilization_score, compute_observed_occupancy_fact
from .sensor_health import compute_sensor_health
from .archetypes import compute_room_archetypes

__all__ = [
    "Settings",
    "get_settings",
    "load_sensors",
    "load_readings",
    "load_spaces",
    "load_timetable",
    "compute_ventilation_metrics",
    "compute_ventilation_risk_score",
    "compute_thermal_comfort",
    "compute_comfort_risk_score",
    "compute_occupancy_analysis",
    "compute_occupancy_utilization_score",
    "compute_observed_occupancy_fact",
    "compute_sensor_health",
    "compute_room_archetypes",
]