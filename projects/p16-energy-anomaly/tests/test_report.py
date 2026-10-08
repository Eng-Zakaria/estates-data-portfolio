"""Tests for output rendering: SVG evidence plot, parquet writers, HTML page."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from anomaly.report import building_page, svg_series, write_anomalies, write_scorecard


def _series(n: int = 200) -> tuple[pd.Series, np.ndarray]:
    ts = pd.Series(pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC"))
    v = np.linspace(1.0, 2.0, n)
    return ts, v


def test_svg_series_contains_polyline_and_bounds() -> None:
    ts, v = _series()
    svg = svg_series(ts, v)
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "<polyline" in svg
    # y is flipped: max value drawn near the top of the frame
    assert "height='180'" in svg


def test_svg_series_marks_flags_and_change_points() -> None:
    ts, v = _series(120)
    mad = np.zeros(120, dtype=bool)
    mad[10] = True
    flat = np.zeros(120, dtype=bool)
    flat[50:70] = True
    svg = svg_series(ts, v, mad_flags=mad, flat_flags=flat, change_points=[30])
    assert svg.count("<circle") == 1
    assert svg.count("<rect") == 1
    assert "<line" in svg


def test_svg_series_downsamples_long_series() -> None:
    ts, v = _series(5000)
    svg = svg_series(ts, v)
    # <= max_points vertices regardless of input length
    assert svg.count(",") < 5000


def test_svg_series_handles_constant_and_missing_series() -> None:
    ts = pd.Series(pd.to_datetime(["2026-01-01 00:00", "2026-01-01 01:00"], utc=True))
    const = np.array([5.0, np.nan])
    svg = svg_series(ts, const)
    assert "<polyline" in svg
    assert svg.endswith("</svg>")


def test_write_anomalies_and_scorecard(tmp_path: Path) -> None:
    rows = [{"meter_id": "M-B001-E01", "kwh_year": 12.0}]
    p1 = write_anomalies(rows, tmp_path / "anomalies.parquet")
    p2 = write_scorecard([{"building": "B001"}], tmp_path / "nested" / "scorecard.parquet")
    assert p1.exists() and p2.exists()
    assert list(pd.read_parquet(p1)["meter_id"]) == ["M-B001-E01"]
    assert list(pd.read_parquet(p2)["building"]) == ["B001"]


def test_building_page_renders_findings_and_synthetic_notice(tmp_path: Path) -> None:
    ts, v = _series(100)
    plot = svg_series(ts, v)
    findings = [
        {
            "type": "high_overnight_baseload",
            "detector": "overnight_rule",
            "start": "2026-01-02T00:00:00+00:00",
            "kwh_day": 1.5,
            "cost_year": 153.36,
            "kgco2e_year": 78.5,
        }
    ]
    out = building_page("B007", findings, plot, "notes here", tmp_path / "B007.html")
    body = out.read_text(encoding="utf-8")
    assert "Synthetic data" in body
    assert "high_overnight_baseload" in body
    assert "£/yr" in body
    assert "<polyline" in body


def test_building_page_currency_switch(tmp_path: Path) -> None:
    out = building_page("BDG2-Orange_Apartments", [], "<svg></svg>", "n", tmp_path / "b.html", currency="$")
    assert "$/yr" in out.read_text(encoding="utf-8")
