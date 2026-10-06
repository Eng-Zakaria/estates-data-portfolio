"""Load COBie and AIR rules from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml


def load_rules(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["rules"]
