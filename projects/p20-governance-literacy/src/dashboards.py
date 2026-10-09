"""Find the KPI names a dashboard actually publishes.

Two sources, both first-party artefacts of the dashboard projects:

* ``projects/pNN-*/powerbi/measures.dax`` - a measure is a line whose last token
  is ``=``: either a bracket measure ``[Total Energy kWh] =`` or a bare
  ``Total Energy kWh =``. DAX keywords (``VAR``, ``RETURN``, ...) are skipped so
  local variables are not mistaken for measures.
* ``projects/pNN-*/src/kpis.py`` - every public function is a KPI helper; it is
  named on a dashboard or in a validation script, so it needs a definition too.

The extraction is deliberately narrow. If a future file needs a wider rule, that
is a change to this module plus its tests, not a hand-maintained list.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

#: DAX words that introduce a local binding rather than a measure.
DAX_KEYWORDS = frozenset(
    {
        "CASE",
        "DEFINE",
        "EVALUATE",
        "IF",
        "IN",
        "MEASURE",
        "ORDER",
        "RETURN",
        "SWITCH",
        "VAR",
        "ORDER BY",
        "FILTER",
        "CALCULATE",
        "SELECTCOLUMNS",
        "SUMMARIZE",
        "TREATAS",
    }
)

_BRACKET_MEASURE = re.compile(r"^\[(?P<name>[^\]\n]+)\]\s*=\s*$")
_COMMENT_MEASURE = re.compile(r"^\s*(?://|--)\s+(?P<name>[^\n=]+?)\s*=\s*$")
#: A definition starts in column 0 and contains `=`. Indented lines are skipped: they
#: are inside a measure body (a `VAR` binding, an argument), not a new measure.
_BARE_MEASURE = re.compile(r"^(?P<name>[A-Za-z][^=\n]*?)\s*=(?:\s*(?P<expr>\S.*))?$")


@dataclass(frozen=True)
class DashboardKpi:
    """One KPI name published by one dashboard."""

    name: str
    project: str
    source: str  # path relative to the repository root

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"{self.project}:{self.name}"


def _is_keyword(name: str) -> bool:
    head = name.strip().split(" ", 1)[0].upper()
    return head in DAX_KEYWORDS or name.strip().upper() in DAX_KEYWORDS


def measure_names(text: str) -> list[str]:
    """Return measure names from DAX source, in file order, without duplicates."""
    found: list[str] = []
    for line in text.splitlines():
        for pattern in (_BRACKET_MEASURE, _COMMENT_MEASURE, _BARE_MEASURE):
            match = pattern.match(line)
            if match:
                name = match.group("name").strip()
                if name and not _is_keyword(name) and name not in found:
                    found.append(name)
                break
    return found


def kpi_function_names(source: str) -> list[str]:
    """Return public top-level function names defined in a Python module."""
    tree = ast.parse(source)
    return [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_")]


def handoff_files(project_dir: Path, repo_root: Path) -> list[tuple[str, Path]]:
    """KPI-bearing files for one project: (kind, path) for ``measures.dax`` and ``src/kpis.py``."""
    out: list[tuple[str, Path]] = []
    dax = project_dir / "powerbi" / "measures.dax"
    if dax.is_file():
        out.append(("measures.dax", dax))
    kpis = project_dir / "src" / "kpis.py"
    if kpis.is_file():
        out.append(("kpis.py", kpis))
    return out


def scan_projects(
    projects_dir: Path,
    repo_root: Path,
    scope: tuple[str, ...],
) -> list[DashboardKpi]:
    """Scan every project in ``scope`` for KPI names.

    Projects with no handoff file contribute nothing; the caller (and the tests)
    decide whether that is acceptable.
    """
    out: list[DashboardKpi] = []
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        project_id = project_dir.name.split("-", 1)[0]
        if project_id not in scope:
            continue
        for kind, path in handoff_files(project_dir, repo_root):
            text = path.read_text(encoding="utf-8", errors="replace")
            names = measure_names(text) if kind == "measures.dax" else kpi_function_names(text)
            rel = path.relative_to(repo_root).as_posix()
            out.extend(DashboardKpi(name=n, project=project_id, source=rel) for n in names)
    return out


def projects_with_handoff(projects_dir: Path) -> dict[str, str]:
    """Map project id -> relative path of its KPI-bearing file, for scope enforcement."""
    out: dict[str, str] = {}
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        files = handoff_files(project_dir, projects_dir.parent)
        if files:
            out[project_dir.name.split("-", 1)[0]] = files[0][1].relative_to(projects_dir.parent).as_posix()
    return out