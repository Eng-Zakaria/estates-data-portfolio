"""P17 CLI integration tests."""

from __future__ import annotations

import pytest
import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """CLI should show help without error."""
    result = subprocess.run([sys.executable, "-m", "src.cli", "--help"], 
                          capture_output=True, text=True, cwd="projects/p17-air-quality-occupancy")
    assert result.returncode == 0
    assert "ventilation" in result.stdout
    assert "comfort" in result.stdout
    assert "occupancy" in result.stdout
    assert "sensor-health" in result.stdout
    assert "archetypes" in result.stdout
    assert "observed-occupancy" in result.stdout
    assert "all" in result.stdout


def test_cli_ventilation():
    """CLI ventilation command should work."""
    result = subprocess.run([
        sys.executable, "-m", "src.cli", "ventilation",
        "--truth-dir", "../../data/truth",
        "--output", "../../data/p17_output/test_vent.parquet"
    ], capture_output=True, text=True, cwd="projects/p17-air-quality-occupancy")
    assert result.returncode == 0
    assert "Ventilation metrics for" in result.stdout


def test_cli_comfort():
    """CLI comfort command should work."""
    result = subprocess.run([
        sys.executable, "-m", "src.cli", "comfort",
        "--truth-dir", "../../data/truth",
        "--output", "../../data/p17_output/test_comfort.parquet"
    ], capture_output=True, text=True, cwd="projects/p17-air-quality-occupancy")
    assert result.returncode == 0
    assert "Thermal comfort metrics for" in result.stdout


def test_cli_occupancy():
    """CLI occupancy command should work."""
    result = subprocess.run([
        sys.executable, "-m", "src.cli", "occupancy",
        "--truth-dir", "../../data/truth",
        "--output", "../../data/p17_output/test_occ.parquet"
    ], capture_output=True, text=True, cwd="projects/p17-air-quality-occupancy")
    assert result.returncode == 0
    assert "Occupancy analysis for" in result.stdout


def test_cli_sensor_health():
    """CLI sensor-health command should work."""
    result = subprocess.run([
        sys.executable, "-m", "src.cli", "sensor-health",
        "--truth-dir", "../../data/truth",
        "--output", "../../data/p17_output/test_health.parquet"
    ], capture_output=True, text=True, cwd="projects/p17-air-quality-occupancy")
    assert result.returncode == 0
    assert "Sensor health for 90 sensors" in result.stdout


def test_cli_archetypes():
    """CLI archetypes command should work."""
    result = subprocess.run([
        sys.executable, "-m", "src.cli", "archetypes",
        "--truth-dir", "../../data/truth",
        "--output", "../../data/p17_output/test_arch.parquet",
        "--n-clusters", "3"
    ], capture_output=True, text=True, cwd="projects/p17-air-quality-occupancy")
    assert result.returncode == 0
    assert "Room archetypes for 500 rooms" in result.stdout


def test_cli_observed_occupancy():
    """CLI observed-occupancy command should work."""
    result = subprocess.run([
        sys.executable, "-m", "src.cli", "observed-occupancy",
        "--truth-dir", "../../data/truth",
        "--output", "../../data/p17_output/test_fact.parquet"
    ], capture_output=True, text=True, cwd="projects/p17-air-quality-occupancy")
    assert result.returncode == 0
    assert "Observed occupancy fact table" in result.stdout