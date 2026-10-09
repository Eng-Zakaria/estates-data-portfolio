"""Load and validate the business glossary, and join it to the DQ scores.

Two jobs:

* keep every entry complete enough to answer "what is this, who owns it, where
  does it come from, how fresh is it, how good is it";
* prove that every KPI a dashboard publishes has a plain-English definition.
  That second one is the acceptance criterion "glossary and metric registry
  cover 100% of dashboard KPIs".
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dashboards import DashboardKpi

REFRESH_VALUES = (
    "hourly",
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "annual",
    "per_release",
    "on_change",
    "static",
)
CLASSIFICATIONS = ("public", "internal", "confidential")


@dataclass(frozen=True)
class Term:
    id: str
    term: str
    definition: str
    owner: str
    source_of_truth: str
    refresh: str
    dataset: str
    classification: str
    notes: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Term:
        return cls(
            id=str(raw["id"]),
            term=" ".join(str(raw["term"]).split()),
            definition=" ".join(str(raw["definition"]).split()),
            owner=str(raw["owner"]),
            source_of_truth=" ".join(str(raw["source_of_truth"]).split()),
            refresh=str(raw["refresh"]),
            dataset=str(raw.get("dataset") or ""),
            classification=str(raw["classification"]),
            notes=" ".join(str(raw.get("notes") or "").split()),
        )


@dataclass(frozen=True)
class Glossary:
    terms: list[Term]
    kpi_aliases: dict[str, str]
    required_terms: tuple[str, ...]
    path: Path

    @property
    def ids(self) -> set[str]:
        return {t.id for t in self.terms}

    def by_id(self) -> dict[str, Term]:
        return {t.id: t for t in self.terms}


def load_glossary(path: Path) -> Glossary:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Glossary(
        terms=[Term.from_dict(t) for t in raw["terms"]],
        kpi_aliases={str(k): str(v) for k, v in (raw.get("kpi_aliases") or {}).items()},
        required_terms=tuple(str(t) for t in (raw.get("required_terms") or [])),
        path=path,
    )


def validate(glossary: Glossary, owner_ids: set[str]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for term in glossary.terms:
        if term.id in seen:
            problems.append(f"{term.id}: duplicate term id")
        seen.add(term.id)
        if term.refresh not in REFRESH_VALUES:
            problems.append(f"{term.id}: refresh {term.refresh!r} not in {REFRESH_VALUES}")
        if term.classification not in CLASSIFICATIONS:
            problems.append(f"{term.id}: classification {term.classification!r} not in {CLASSIFICATIONS}")
        if term.owner not in owner_ids:
            problems.append(f"{term.id}: owner {term.owner!r} is not declared in metrics.yml owners")
        if not term.definition or not term.source_of_truth:
            problems.append(f"{term.id}: definition and source_of_truth must be filled in")
    for required in glossary.required_terms:
        if required not in glossary.ids:
            problems.append(f"required term {required!r} is missing from the glossary")
    for kpi, target in glossary.kpi_aliases.items():
        if target not in glossary.ids:
            problems.append(f"kpi_aliases[{kpi!r}] points at unknown term {target!r}")
    return problems


def coverage_problems(glossary: Glossary, kpis: list[DashboardKpi]) -> list[str]:
    """The alias table must match the dashboard KPI set exactly, both ways."""
    problems: list[str] = []
    kpi_names = {k.name for k in kpis}
    aliased = set(glossary.kpi_aliases)

    for name in sorted(kpi_names - aliased):
        projects = sorted({k.project for k in kpis if k.name == name})
        problems.append(f"dashboard KPI {name!r} ({', '.join(projects)}) has no glossary definition")
    for name in sorted(aliased - kpi_names):
        problems.append(f"glossary.kpi_aliases has {name!r}, which no dashboard publishes")
    return problems


def load_dq_scores(path: Path) -> dict[str, float]:
    """dataset -> score from the P03 output. Empty dict when the run has not happened."""
    if not path.is_file():
        return {}
    scores: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("grain") != "dataset" or not row.get("dataset"):
                continue
            try:
                scores[row["dataset"]] = float(row["score"])
            except (KeyError, TypeError, ValueError):
                continue
    return scores


def dq_score_for(term: Term, scores: dict[str, float]) -> str:
    """Human-readable current DQ score for a term, or an honest 'not measured'."""
    if not scores:
        return "not measured in this checkout"
    if not term.dataset:
        return "concept, not dataset-scored"
    if term.dataset not in scores:
        return f"dataset {term.dataset} not scored"
    return f"{scores[term.dataset]:.1f}/100 ({term.dataset}, run output)"