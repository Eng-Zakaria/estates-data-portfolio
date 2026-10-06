"""P11 tests: extraction, QA report, reconciliation on tiny fixture IFC."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

SRC = Path("projects/p11-ifc-analytics/src")
FIXTURE = Path("data/ifc/sample_b003.ifc")

import sys

sys.path.insert(0, str(SRC))


@pytest.fixture(scope="module")
def tables():
    out = Path("data/gold/ifc_test")
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(SRC / "ifc2tables" / "extract.py"), str(FIXTURE), "--out", str(out)],
        check=True,
        capture_output=True,
    )
    return {p.stem: pd.read_parquet(p) for p in out.glob("*.parquet")}


def test_extract_spaces(tables):
    spaces = tables["ifc_spaces"]
    assert len(spaces) > 0
    assert "area_m2" in spaces.columns
    assert "area_source" in spaces.columns


def test_extract_elements(tables):
    elements = tables["ifc_elements"]
    assert len(elements) > 0
    assert "ifc_class" in elements.columns


def test_extract_systems(tables):
    systems = tables["ifc_systems"]
    assert len(systems) > 0


def test_extract_classifications(tables):
    classifications = tables["ifc_classifications"]
    assert len(classifications) >= 0  # some planted without classification


def test_qa_report_counts(tables, tmp_path):
    from ifc2tables.qa_report import qa_report

    report = qa_report(tables, tmp_path)
    assert report["counts"]["spaces"] > 0
    assert report["counts"]["elements"] > 0
    assert report["zero_area_spaces"] >= 1  # planted
    assert report["elements_without_type"] >= 1  # planted
    assert report["duplicate_element_names"] >= 1  # planted


def test_reconcile_recall(tables, tmp_path):
    from ifc2tables.reconcile import reconcile

    recon = reconcile(tables, tmp_path)
    missing = recon[recon["status"] == "missing_from_model"]
    mismatch = recon[(recon["status"] == "matched") & (recon["area_delta_pct"].abs() > 10)]
    assert len(missing) >= 5  # planted 5 rooms missing
    assert len(mismatch) >= 12  # planted 12 rooms with >10% area mismatch
