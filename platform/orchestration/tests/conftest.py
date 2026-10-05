"""P02 host-test path bootstrap (tasks importable without airflow installed)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
