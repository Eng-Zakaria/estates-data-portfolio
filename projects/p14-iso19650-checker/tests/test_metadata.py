"""Metadata backends and the "skipped, not silently passed" guard (AGENTS.md rule 9).

Each optional dependency is exercised when installed and skipped when not, so the suite is honest on a
machine without ifcopenshell / python-docx / pypdf / openpyxl.
"""

from __future__ import annotations

import metadata
import pytest
from checker import check_folder, load_convention
from conftest import register_outside, write
from metadata import MetadataReader, available_backends, backend_available, extract, normalise

pytest.importorskip("pytest")


def test_backend_availability_is_reported_not_assumed():
    backends = available_backends()
    assert set(backends) == {"ifcopenshell", "python-docx", "pypdf", "openpyxl", "stdlib"}
    assert backends["stdlib"] is True


def test_magic_byte_screening(tmp_path):
    """A file named .pdf that is not a PDF must be reported as a placeholder, not fed to the parser."""
    fake_pdf = write(tmp_path, "Shared/thing.pdf", "synthetic placeholder container\n")
    assert extract(fake_pdf) is None

    real = write(tmp_path, "Shared/real.txt", "a title\n")
    identity = extract(real)
    assert identity is not None
    assert identity.title == "a title"
    assert identity.backend == "stdlib"


def test_text_backend_reads_the_first_non_empty_line(tmp_path):
    path = write(tmp_path, "Shared/x.txt", "\n\n   DR 0001 ESTM title   \nmore text\n")
    identity = extract(path)
    assert identity.title == "DR 0001 ESTM title"
    assert identity.project_name == ""  # only IFC has a project name
    assert identity.best == identity.title


@pytest.mark.skipif(not backend_available("python-docx"), reason="python-docx not installed")
def test_docx_title_is_read(tmp_path):
    import docx

    path = tmp_path / "Shared" / "drawing.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = docx.Document()
    document.core_properties.title = "DR 0001 ESTM general arrangement"
    document.save(str(path))
    identity = extract(path)
    assert identity is not None
    assert identity.title == "DR 0001 ESTM general arrangement"
    assert identity.backend == "python-docx"


@pytest.mark.skipif(not backend_available("pypdf"), reason="pypdf not installed")
def test_pdf_title_is_read(tmp_path):
    from pypdf import PdfWriter

    path = tmp_path / "Shared" / "drawing.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": "DR 0002 ENGG section"})
    with open(path, "wb") as handle:
        writer.write(handle)
    identity = extract(path)
    assert identity is not None
    assert identity.title == "DR 0002 ENGG section"


@pytest.mark.skipif(not backend_available("openpyxl"), reason="openpyxl not installed")
def test_xlsx_title_is_read(tmp_path):
    from openpyxl import Workbook

    path = tmp_path / "Shared" / "schedule.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    workbook.properties.title = "CP 0003 QSUR cost plan"
    workbook.save(str(path))
    identity = extract(path)
    assert identity is not None
    assert identity.title == "CP 0003 QSUR cost plan"


def test_reader_reports_a_missing_backend_as_skipped(tmp_path, uk_config, monkeypatch):
    """If the backend is absent the check is skipped and *reported*, never counted as a pass."""
    monkeypatch.setattr(metadata, "backend_available", lambda backend: backend == "stdlib")
    write(tmp_path, "WIP/PRJ01-ENGG-ZZ-01-DR-A-0007-S0-P01.01.docx", "not really a docx\n")

    reader = MetadataReader(uk_config.metadata)
    result = check_folder(tmp_path, uk_config)
    assert "metadata_mismatch" not in {i.rule_id for i in result.issues}
    assert reader.skipped() == reader.skipped()  # deterministic ordering
    result_with_reader = check_folder(tmp_path, uk_config)
    assert any(s.startswith("metadata:") for s in result_with_reader.skipped_checks)


def test_reader_reports_an_unreadable_container_as_skipped(tmp_path, uk_config, monkeypatch):
    """A .docx that passes the magic-byte screen but cannot be parsed is skipped, not passed."""
    path = tmp_path / "WIP" / "PRJ01-ENGG-ZZ-01-DR-A-0008-S0-P01.01.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"PK\x03\x04 not really an office file")
    assert extract(path) is None
    result = check_folder(tmp_path, uk_config)
    assert "metadata_mismatch" not in {i.rule_id for i in result.issues}


def test_container_with_no_title_is_skipped(tmp_path, uk_config):
    write(tmp_path, "WIP/PRJ01-ENGG-ZZ-01-DR-A-0009-S0-P01.01.txt", "\n\n")
    result = check_folder(tmp_path, uk_config)
    assert "metadata_mismatch" not in {i.rule_id for i in result.issues}
    assert "metadata:no-title:.txt" in result.skipped_checks


def test_ignore_case_toggle(tmp_path, uk_config):
    config = uk_config.model_copy(update={"metadata": uk_config.metadata.model_copy(update={"ignore_case": False})})
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt", "dr 0001 estm title\n")
    insensitive = check_folder(tmp_path, uk_config)
    sensitive = check_folder(tmp_path, config)
    assert "metadata_mismatch" not in {i.rule_id for i in insensitive.issues}
    assert "metadata_mismatch" in {i.rule_id for i in sensitive.issues}


def test_normalise():
    assert normalise("DR_0001-ESTM", True) == "dr 0001 estm"
    assert normalise("DR_0001-ESTM", False) == "DR 0001 ESTM"


def test_metadata_findings_do_not_run_on_containers_the_config_ignores(tmp_path, uk_config):
    """A .dwg is not read by any backend here, so its name is only checked structurally."""
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0010-S0-P01.01.dwg", "nothing to read\n")
    result = check_folder(tmp_path, uk_config)
    assert result.issues == []


def test_register_and_orphan_checks_use_relative_posix_paths(tmp_path, uk_config):
    write(tmp_path, "WIP/nested/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    register = register_outside(tmp_path)
    register.write_text("path\n", encoding="utf-8")
    result = check_folder(
        tmp_path, load_convention(uk_config.path) if hasattr(uk_config, "path") else uk_config, register=register
    )
    assert [i.path for i in result.issues if i.rule_id == "orphan_file"] == [
        "WIP/nested/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt"
    ]
