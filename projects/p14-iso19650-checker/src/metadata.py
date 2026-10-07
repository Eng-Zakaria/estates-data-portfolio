"""Optional metadata extraction for consistency checks (filename vs document identity).

Every backend is imported lazily and separately: if `ifcopenshell`, `python-docx`, `pypdf` or
`openpyxl` is not installed the corresponding check is *skipped and reported as skipped*, never
silently passed (AGENTS.md hard rule 9: honest metrics).

Backends
    ifc / ifczip  ifcopenshell  -> IFC header `project_name`, `name`, `author`, `organization`, `originating_system`
    docx          python-docx   -> core properties `title`
    pdf           pypdf         -> document metadata `title` / `subject`
    xlsx          openpyxl      -> workbook properties `title`
    txt / md      stdlib        -> first non-empty line (so the sample generator and tests can seed a
                                   title mismatch without any third-party dependency)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from checker import ERROR, Issue, MetadataRules

IFC_SUFFIXES = {".ifc", ".ifczip"}
DOCX_SUFFIXES = {".docx"}
PDF_SUFFIXES = {".pdf"}
XLSX_SUFFIXES = {".xlsx"}
TEXT_SUFFIXES = {".txt", ".md"}


@dataclass
class DocumentIdentity:
    """What we managed to read out of a container."""

    title: str = ""
    project_name: str = ""
    backend: str = ""

    @property
    def best(self) -> str:
        return self.project_name or self.title


def _backend_for(suffix: str) -> str:
    if suffix in IFC_SUFFIXES:
        return "ifcopenshell"
    if suffix in DOCX_SUFFIXES:
        return "python-docx"
    if suffix in PDF_SUFFIXES:
        return "pypdf"
    if suffix in XLSX_SUFFIXES:
        return "openpyxl"
    if suffix in TEXT_SUFFIXES:
        return "stdlib"
    return ""


def _read_ifc(path: Path) -> DocumentIdentity:
    import ifcopenshell  # noqa: PLC0415 - optional dependency, imported lazily on purpose

    model = ifcopenshell.open(str(path))
    header = model.header
    name = getattr(getattr(header, "file_name", None), "project_name", "") or ""
    return DocumentIdentity(
        title=str(name),
        project_name=str(name),
        backend="ifcopenshell",
    )


def _read_docx(path: Path) -> DocumentIdentity:
    import docx  # noqa: PLC0415 - optional dependency

    core = docx.Document(str(path)).core_properties
    return DocumentIdentity(title=str(core.title or ""), backend="python-docx")


def _read_pdf(path: Path) -> DocumentIdentity:
    from pypdf import PdfReader  # noqa: PLC0415 - optional dependency

    info = PdfReader(str(path)).metadata or {}
    return DocumentIdentity(title=str(info.get("/Title") or ""), backend="pypdf")


def _read_xlsx(path: Path) -> DocumentIdentity:
    from openpyxl import load_workbook  # noqa: PLC0415 - optional dependency

    props = load_workbook(str(path), read_only=True).properties
    return DocumentIdentity(title=str(props.title or ""), backend="openpyxl")


def _read_text(path: Path) -> DocumentIdentity:
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                return DocumentIdentity(title=line.strip(), backend="stdlib")
    return DocumentIdentity(backend="stdlib")


READERS = {
    "ifcopenshell": _read_ifc,
    "python-docx": _read_docx,
    "pypdf": _read_pdf,
    "openpyxl": _read_xlsx,
    "stdlib": _read_text,
}


def backend_available(backend: str) -> bool:
    if backend == "ifcopenshell":
        import importlib.util

        return importlib.util.find_spec("ifcopenshell") is not None
    if backend == "python-docx":
        import importlib.util

        return importlib.util.find_spec("docx") is not None
    if backend == "pypdf":
        import importlib.util

        return importlib.util.find_spec("pypdf") is not None
    if backend == "openpyxl":
        import importlib.util

        return importlib.util.find_spec("openpyxl") is not None
    return backend == "stdlib"


def _looks_like_container(path: Path, backend: str) -> bool:
    """Cheap magic-byte screen so a mislabelled placeholder does not spam the parsers.

    Synthetic samples and real exports differ here: a `.pdf` that does not start with `%PDF` is not a
    PDF, and saying so is more honest than reporting a parser failure.
    """
    try:
        with open(path, "rb") as handle:
            head = handle.read(512)
    except OSError:  # pragma: no cover - unreadable file
        return False
    if backend == "pypdf":
        return head.startswith(b"%PDF")
    if backend in {"python-docx", "openpyxl"}:
        return head.startswith(b"PK\x03\x04")
    if backend == "ifcopenshell":
        return b"ISO-10303" in head or head.startswith(b"PK\x03\x04") or head.lstrip()[:1] in {b"#", b"*"}
    return True


def available_backends() -> dict[str, bool]:
    return {name: backend_available(name) for name in READERS}


def extract(path: Path) -> DocumentIdentity | None:
    """Read a container's declared identity, or None if no backend can read it."""
    backend = _backend_for(path.suffix.lower())
    if not backend or not backend_available(backend):
        return None
    if not _looks_like_container(path, backend):
        return None
    if backend == "pypdf":
        # pypdf logs loudly on malformed input; the magic-byte screen already ran, keep it quiet.
        import logging

        logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    try:
        return READERS[backend](path)
    except Exception:  # noqa: BLE001 - a corrupt container is not a checker crash
        return None


def normalise(text: str, ignore_case: bool) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", text)
    return cleaned.casefold() if ignore_case else cleaned


class MetadataReader:
    """Compares what the file name claims with what the container itself declares."""

    def __init__(self, rules: MetadataRules) -> None:
        self.rules = rules
        self._skipped: set[str] = set()

    def skipped(self) -> list[str]:
        return sorted(self._skipped)

    def _wanted(self, suffix: str) -> bool:
        if suffix in IFC_SUFFIXES:
            return self.rules.compare_ifc_project_name
        if suffix in DOCX_SUFFIXES or suffix in PDF_SUFFIXES or suffix in XLSX_SUFFIXES:
            return self.rules.compare_doc_title
        return suffix in TEXT_SUFFIXES

    def check(
        self,
        path: Path,
        parts: list[str],
        config: object,
        shown: str,
        container_id: str,
    ) -> list[Issue]:
        suffix = path.suffix.lower()
        if not self._wanted(suffix):
            return []
        backend = _backend_for(suffix)
        if backend and not _looks_like_container(path, backend):
            self._skipped.add(f"metadata:placeholder:{suffix}")
            return []
        identity = extract(path)
        if identity is None:
            if backend and not backend_available(backend):
                self._skipped.add(f"metadata:{backend}")
            else:
                self._skipped.add(f"metadata:unreadable:{suffix}")
            return []
        declared = normalise(identity.best, self.rules.ignore_case)
        if not declared:
            self._skipped.add(f"metadata:no-title:{suffix}")
            return []
        haystack = f" {declared} "
        issues: list[Issue] = []
        for name in self.rules.required_title_fields:
            spec = config.field_by_name(name)  # type: ignore[attr-defined]
            if spec is None or spec.position >= len(parts):
                continue
            token = parts[spec.position]
            if not token:
                continue
            normalised = normalise(token, self.rules.ignore_case)
            if normalised and f" {normalised} " not in haystack:
                issues.append(
                    Issue(
                        shown,
                        "metadata_mismatch",
                        ERROR,
                        f"{name} '{token}' does not appear in the container's "
                        f"{'IFC project name' if identity.project_name else 'document title'} "
                        f"'{identity.best}' (read via {identity.backend})",
                        field=name,
                        container_id=container_id,
                    )
                )
        return issues
