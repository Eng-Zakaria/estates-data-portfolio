"""Shared fixtures for the P14 tests.

Tests import the checker from `src/` by path (the project is not installed as a package) and build
small, hand-checked folder trees in tmp_path so every assertion is about a name someone can read.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

UK_CONVENTION = PROJECT / "conventions" / "uk_national_annex.yml"
VARIANT_CONVENTION = PROJECT / "conventions" / "estates_cde_variant.yml"

# A deliberately tiny convention for unit tests: 3 fields, one code list, one state folder. Nothing
# here is a real-world codification; it exists to pin the engine's behaviour precisely.
MINIMAL_CONVENTION = """
name: unit_test_minimal
description: three fields, one state folder
separator: "-"
case: upper
id_fields: [project, kind, number]
extension_allowlist: [.txt]
illegal_characters: [" ", "_"]
path_max_length: 120
max_stem_length: 30
container_states:
  WIP: ["S0"]
fields:
  - name: project
    position: 0
    length: 4
    charset: "A-Z0-9"
  - name: kind
    position: 1
    charset: "A-Z"
    allowed_values: ["DR", "RP"]
  - name: number
    position: 2
    length: 4
    charset: "0-9"
  - name: status
    position: 3
    pattern: "S[0-6]"
sequence:
  field: number
  scope: folder
  warn_on_gap: true
revision:
  field: null
  warn_on_gap: false
metadata:
  enabled: false
"""


@pytest.fixture
def minimal_config():
    from checker import load_convention_text

    return load_convention_text(MINIMAL_CONVENTION)


@pytest.fixture
def uk_config():
    from checker import load_convention

    return load_convention(UK_CONVENTION)


@pytest.fixture
def variant_config():
    from checker import load_convention

    return load_convention(VARIANT_CONVENTION)


def write(root: Path, relative: str, content: str | None = None) -> Path:
    """Create a file (and its parents).

    The default body repeats the file name as its title, so a fixture is metadata-clean unless the test
    deliberately passes a title that disagrees with the name.
    """
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if content is None:
        title = " ".join(part for part in path.stem.replace("-", " ").replace("_", " ").split() if part)
        content = f"{title}\n\nsynthetic placeholder\n"
    path.write_text(content, encoding="utf-8")
    return path


def register_outside(tmp_path: Path, name: str = "register.csv") -> Path:
    """A register file that is *not* inside the tree being checked.

    A register kept inside the scanned folder would itself be a naming violation and an orphan.
    """
    sidecar = tmp_path.parent / f"{tmp_path.name}_sidecar"
    sidecar.mkdir(exist_ok=True)
    return sidecar / name
