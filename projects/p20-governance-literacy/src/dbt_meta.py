"""Read the dbt project without a compiled manifest.

``manifest.json`` is a build artefact and is not committed, so the dictionary and
lineage pages are built from two first-party sources instead:

* the YAML files in ``platform/dbt/models`` - model names, descriptions, column
  types, descriptions and tests, plus sources and exposures;
* the model SQL itself - ``{{ ref('x') }}`` and ``{{ source('a', 'b') }}`` give
  the edges.

If a real ``manifest.json`` ever lands in ``platform/dbt/target``, it is read
first (it is the authoritative dbt answer), and the YAML/SQL path remains as the
offline fallback. Both paths are exercised by tests on fixtures.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_REF = re.compile(r"\{\{\s*ref\(\s*'([^']+)'\s*\)\s*\}\}")
_REF2 = re.compile(r"\{\{\s*ref\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)\s*\}\}")
_SOURCE = re.compile(r"\{\{\s*source\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)\s*\}\}")

LAYERS = ("staging", "intermediate", "marts")


@dataclass
class Column:
    name: str
    data_type: str
    description: str
    tests: list[str] = field(default_factory=list)


@dataclass
class Model:
    name: str
    description: str
    layer: str
    materialization: str = ""
    columns: list[Column] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)


@dataclass
class Exposure:
    name: str
    description: str
    type: str
    owner: str
    depends_on: list[str]


@dataclass
class DbtMetadata:
    models: list[Model]
    exposures: list[Exposure]
    source: str  # "manifest" | "yaml+sql"
    manifest_found: bool = False

    @property
    def by_name(self) -> dict[str, Model]:
        return {m.name: m for m in self.models}

    @property
    def edges(self) -> list[tuple[str, str]]:
        """(upstream, downstream) pairs for models, plus exposure dependencies."""
        out: list[tuple[str, str]] = []
        known = set(self.by_name)
        for model in self.models:
            for parent in model.depends_on:
                if parent in known:
                    out.append((parent, model.name))
        for exposure in self.exposures:
            for parent in exposure.depends_on:
                if parent in known:
                    out.append((parent, exposure.name))
        return sorted(set(out))


def _test_names(raw: Any) -> list[str]:
    """Flatten dbt test entries (strings or {test: {arguments: ...}} maps) to names."""
    out: list[str] = []
    if raw is None:
        return out
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, dict):
        return [str(k) for k in raw]
    for item in raw:
        out.extend(_test_names(item))
    return out


def _layer_from_path(yml: Path, models_dir: Path) -> str:
    stem = yml.stem
    if stem in LAYERS:
        return stem
    if stem == "seeds":
        return "seeds"
    if stem == "snapshots":
        return "snapshots"
    return "other"


def from_yaml_and_sql(models_dir: Path) -> DbtMetadata:
    """Build metadata from the model YAML files and the SQL that references them."""
    models: dict[str, Model] = {}
    exposures: list[Exposure] = []

    for yml in sorted(models_dir.glob("*.yml")):
        raw = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        layer = _layer_from_path(yml, models_dir)
        for section, materialization in (("models", ""), ("seeds", "seed"), ("snapshots", "snapshot")):
            for entry in raw.get(section) or []:
                name = str(entry.get("name"))
                columns = [
                    Column(
                        name=str(c.get("name")),
                        data_type=str(c.get("data_type") or ""),
                        description=" ".join(str(c.get("description") or "").split()),
                        tests=_test_names(c.get("tests")),
                    )
                    for c in entry.get("columns") or []
                ]
                models[name] = Model(
                    name=name,
                    description=" ".join(str(entry.get("description") or "").split()),
                    layer=layer,
                    materialization=materialization,
                    columns=columns,
                    tests=_test_names(entry.get("tests")),
                )
        for entry in raw.get("exposures") or []:
            depends: list[str] = []
            for dep in entry.get("depends_on") or []:
                match = re.search(r"ref\(\s*'([^']+)'", str(dep))
                if match:
                    depends.append(match.group(1))
            exposures.append(
                Exposure(
                    name=str(entry.get("name")),
                    description=" ".join(str(entry.get("description") or "").split()),
                    type=str(entry.get("type") or ""),
                    owner=str((entry.get("owner") or {}).get("name") or ""),
                    depends_on=depends,
                )
            )

    for sql in sorted(models_dir.rglob("*.sql")):
        name = sql.stem
        text = sql.read_text(encoding="utf-8", errors="replace")
        if name not in models:
            models[name] = Model(name=name, description="", layer=_layer_from_dir(models_dir, sql))
        model = models[name]
        materialization = re.search(r"materialized\s*=\s*'(\w+)'", text)
        if materialization:
            model.materialization = materialization.group(1)
        parents = {m.group(1) for m in _REF.finditer(text)}
        parents |= {m.group(2) for m in _REF2.finditer(text)}
        parents |= {f"{m.group(1)}.{m.group(2)}" for m in _SOURCE.finditer(text)}
        model.depends_on = sorted(parents)

    return DbtMetadata(models=sorted(models.values(), key=lambda m: m.name), exposures=exposures, source="yaml+sql")


def _layer_from_dir(models_dir: Path, path: Path) -> str:
    rel = path.relative_to(models_dir)
    return rel.parts[0] if len(rel.parts) > 1 else "other"


def from_manifest(manifest_path: Path) -> DbtMetadata:
    """Build metadata from a compiled dbt manifest (authoritative when present)."""
    raw: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    models: list[Model] = []
    for node in raw.get("nodes", {}).values():
        if node.get("resource_type") not in ("model", "seed", "snapshot"):
            continue
        columns = [
            Column(
                name=name,
                data_type=str((info.get("type") or "")),
                description=" ".join(str(info.get("description") or "").split()),
            )
            for name, info in sorted((node.get("columns") or {}).items())
        ]
        models.append(
            Model(
                name=str(node["name"]),
                description=" ".join(str(node.get("description") or "").split()),
                layer=str(node.get("path") or "other").split("/")[0],
                materialization=str(node.get("config", {}).get("materialized") or ""),
                columns=columns,
                depends_on=sorted(node.get("depends_on", {}).get("nodes", [])),
            )
        )
    exposures = [
        Exposure(
            name=str(node["name"]),
            description=" ".join(str(node.get("description") or "").split()),
            type=str(node.get("type") or ""),
            owner=str((node.get("owner") or {}).get("name") or ""),
            depends_on=sorted(node.get("depends_on", {}).get("nodes", [])),
        )
        for node in raw.get("exposures", {}).values()
    ]
    return DbtMetadata(models=sorted(models, key=lambda m: m.name), exposures=exposures, source="manifest", manifest_found=True)


def load(models_dir: Path, manifest_path: Path | None = None) -> DbtMetadata:
    """Manifest if it exists, otherwise YAML + SQL. Never raises on missing dirs."""
    if manifest_path and manifest_path.is_file():
        return from_manifest(manifest_path)
    if not models_dir.is_dir():
        return DbtMetadata(models=[], exposures=[], source="yaml+sql")
    return from_yaml_and_sql(models_dir)