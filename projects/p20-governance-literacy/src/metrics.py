"""Load and validate the metric registry, then check it against the dashboards.

The registry (``metrics.yml``) is the answer to "what does this number mean?".
The dashboards are the answer to "what numbers do we publish?". This module
makes those two sets testable against each other in both directions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dashboards import DashboardKpi

REQUIRED_FIELDS = (
    "id",
    "name",
    "kind",
    "status",
    "definition",
    "formula",
    "grain",
    "owner",
    "source_model",
    "caveats",
    "version",
    "dashboards",
    "glossary_term",
    "classification",
)
KINDS = ("metric", "helper")
STATUSES = ("live", "planned")
CLASSIFICATIONS = ("public", "internal", "confidential")

#: `source_model` prefixes that mean "not a dbt model": a repo file or a P03 output.
EXTERNAL_SOURCE_PREFIXES = ("file:", "dq:")


@dataclass(frozen=True)
class Metric:
    id: str
    name: str
    kind: str
    status: str
    definition: str
    formula: str
    grain: str
    owner: str
    source_model: list[str]
    caveats: list[str]
    version: str
    dashboards: list[str]
    glossary_term: str
    classification: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Metric:
        return cls(
            id=str(raw["id"]),
            name=str(raw["name"]),
            kind=str(raw["kind"]),
            status=str(raw["status"]),
            definition=" ".join(str(raw["definition"]).split()),
            formula=" ".join(str(raw["formula"]).split()),
            grain=" ".join(str(raw["grain"]).split()),
            owner=str(raw["owner"]),
            source_model=[str(s) for s in raw["source_model"]],
            caveats=[" ".join(str(c).split()) for c in raw["caveats"]],
            version=str(raw["version"]),
            dashboards=[str(d) for d in raw["dashboards"]],
            glossary_term=str(raw["glossary_term"]),
            classification=str(raw["classification"]),
        )


@dataclass(frozen=True)
class Registry:
    metrics: list[Metric]
    owner_ids: tuple[str, ...]
    path: Path

    @property
    def by_name(self) -> dict[str, Metric]:
        return {m.name: m for m in self.metrics}

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(m.id for m in self.metrics)

    @property
    def live(self) -> list[Metric]:
        return [m for m in self.metrics if m.status == "live"]

    @property
    def planned(self) -> list[Metric]:
        return [m for m in self.metrics if m.status == "planned"]

    def consumers(self) -> set[str]:
        return {c for m in self.metrics for c in m.dashboards}


def load_registry(path: Path) -> Registry:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    metrics = [Metric.from_dict(m) for m in raw["metrics"]]
    owners = tuple(str(o["id"]) for o in raw["owners"])
    return Registry(metrics=metrics, owner_ids=owners, path=path)


def validate(registry: Registry, glossary_term_ids: set[str], known_consumers: set[str]) -> list[str]:
    """Return a list of problems. Empty list means the registry is well formed."""
    problems: list[str] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for m in registry.metrics:
        if m.kind not in KINDS:
            problems.append(f"{m.id}: kind {m.kind!r} not in {KINDS}")
        if m.status not in STATUSES:
            problems.append(f"{m.id}: status {m.status!r} not in {STATUSES}")
        if m.classification not in CLASSIFICATIONS:
            problems.append(f"{m.id}: classification {m.classification!r} not in {CLASSIFICATIONS}")
        if m.id in seen_ids:
            problems.append(f"{m.id}: duplicate id")
        seen_ids.add(m.id)
        if m.name in seen_names:
            problems.append(f"{m.id}: duplicate name {m.name!r}")
        seen_names.add(m.name)
        if m.owner not in registry.owner_ids:
            problems.append(f"{m.id}: owner {m.owner!r} is not declared in owners")
        if m.glossary_term not in glossary_term_ids:
            problems.append(f"{m.id}: glossary_term {m.glossary_term!r} has no glossary entry")
        if not m.definition or not m.formula or not m.grain or not m.version:
            problems.append(f"{m.id}: definition, formula, grain and version must all be filled in")
        if m.kind == "metric" and not m.source_model:
            problems.append(f"{m.id}: a metric must name at least one source model")
        unknown = [c for c in m.dashboards if c not in known_consumers]
        if unknown:
            problems.append(f"{m.id}: unknown consumer(s) {unknown}")
        if not m.dashboards and m.status != "planned":
            problems.append(f"{m.id}: a live metric must name at least one consumer, or be status planned")
        if m.status == "planned" and not m.caveats:
            problems.append(f"{m.id}: a planned metric must say why it is not published yet")
    for owner_id in registry.owner_ids:
        if not any(m.owner == owner_id for m in registry.metrics):
            problems.append(f"owner {owner_id!r} owns no metric; remove it or document the domain")
    return problems


def coverage_problems(registry: Registry, kpis: list[DashboardKpi]) -> list[str]:
    """Both directions of the "every dashboard KPI is registered" rule."""
    problems: list[str] = []
    by_name = registry.by_name
    registered_names = set(by_name)
    kpi_names = {k.name for k in kpis}

    for name in sorted(kpi_names - registered_names):
        projects = sorted({k.project for k in kpis if k.name == name})
        problems.append(f"dashboard KPI {name!r} ({', '.join(projects)}) has no metrics.yml entry")

    for name in sorted(registered_names - kpi_names):
        metric = by_name[name]
        if metric.status != "planned":
            problems.append(
                f"metrics.yml entry {metric.id!r} ({name!r}) is {metric.status!r} but no dashboard publishes it"
            )

    for name in sorted(kpi_names & registered_names):
        metric = by_name[name]
        declared = set(metric.dashboards)
        actual = {k.project for k in kpis if k.name == name}
        if not declared & actual:
            problems.append(
                f"metrics.yml entry {metric.id!r} is not attributed to the project that publishes it ({sorted(actual)})"
            )
    return problems


def dbt_model_names(models_dir: Path) -> set[str]:
    """Model and seed names declared in the dbt YAML files (used to validate source_model)."""
    names: set[str] = set()
    for yml in sorted(models_dir.glob("*.yml")):
        raw = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        for section in ("models", "seeds", "snapshots"):
            for entry in raw.get(section) or []:
                if entry.get("name"):
                    names.add(str(entry["name"]))
    return names


def source_model_problems(registry: Registry, models_dir: Path) -> list[str]:
    """`source_model` entries that look like dbt models must exist as dbt models."""
    known = dbt_model_names(models_dir)
    problems: list[str] = []
    for metric in registry.metrics:
        for source in metric.source_model:
            if source.startswith(EXTERNAL_SOURCE_PREFIXES):
                continue
            if source not in known:
                problems.append(f"{metric.id}: source_model {source!r} is not a dbt model in {models_dir.name}/")
    return problems