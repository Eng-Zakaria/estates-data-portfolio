"""Contract loading (YAML) + catalogue generation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class ContractColumn(BaseModel):
    name: str
    type: str = "string"
    nullable: bool = True
    description: str = ""
    allowed: list[str] | None = None


class Contract(BaseModel):
    source: str
    business_key: list[str] = []
    description: str = ""
    columns: list[ContractColumn] = []
    date_candidates: list[str] = []
    units: dict[str, str] = {}


def contract_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts"


def load_contract(source: str) -> Contract:
    path = contract_dir() / f"{source}.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Contract(**data)


def list_contracts() -> list[Contract]:
    return [load_contract(p.stem) for p in sorted(contract_dir().glob("*.yml"))]


def generate_catalogue_md(out: Path) -> Path:
    lines = [
        "# Catalogue (generated from contracts)",
        "",
        "> Synthetic source-system extracts. Truth is synthetic.",
        "",
    ]
    for c in list_contracts():
        lines += [f"## {c.source}", "", f"{c.description}", "", f"Business key: `{', '.join(c.business_key)}`", ""]
        lines += ["| column | type | nullable | description |", "|---|---|---|---|"]
        for col in c.columns:
            lines.append(f"| {col.name} | {col.type} | {col.nullable} | {col.description} |")
        lines += [""]
        if c.date_candidates:
            lines += [f"Date candidates: {', '.join(f'`{d}`' for d in c.date_candidates)}", ""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
