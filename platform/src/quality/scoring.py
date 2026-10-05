"""P03 scoring: weighted DQ scores per dataset / dimension / building.

score = 100 * sum(w * pass_rate) / sum(w) with severity weights error=3,
warn=2, info=1 (weights live in spec.SEVERITY_WEIGHTS). Status of a check is
pass iff pass_rate >= threshold; the score itself stays continuous so trends
are meaningful. Building scores use only ``by_building`` checks, whose
per-building (checked, failed) pairs come from the SQL engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from .spec import CheckSpec


@dataclass
class CheckOutcome:
    check_id: str
    dataset: str
    dimension: str
    severity: str
    pass_rate: float
    threshold: float
    by_building: dict[str, dict[str, int]] | None = None

    @property
    def status(self) -> str:
        return "pass" if self.pass_rate * 100.0 >= self.threshold else "fail"


def _weighted(parts: list[tuple[float, float]]) -> float:
    num = sum(w * r for w, r in parts)
    den = sum(w for w, _ in parts)
    return 100.0 * num / den if den > 0 else 100.0


def dataset_scores(specs: dict[str, CheckSpec], outcomes: dict[str, CheckOutcome]) -> dict[str, tuple[float, int]]:
    """Map dataset -> (score, n_checks)."""
    by_ds: dict[str, list[tuple[float, float]]] = {}
    for cid, o in outcomes.items():
        by_ds.setdefault(o.dataset, []).append((specs[cid].weight, o.pass_rate))
    return {d: (_weighted(v), len(v)) for d, v in by_ds.items()}


def dimension_scores(
    specs: dict[str, CheckSpec], outcomes: dict[str, CheckOutcome]
) -> dict[tuple[str, str], tuple[float, int]]:
    """Map (dataset, dimension) -> (score, n_checks)."""
    by_dim: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for cid, o in outcomes.items():
        by_dim.setdefault((o.dataset, o.dimension), []).append((specs[cid].weight, o.pass_rate))
    return {k: (_weighted(v), len(v)) for k, v in by_dim.items()}


def building_scores(specs: dict[str, CheckSpec], outcomes: dict[str, CheckOutcome]) -> dict[str, tuple[float, int]]:
    """Map building_id -> (score, n_checks) over by_building checks only."""
    by_b: dict[str, list[tuple[float, float]]] = {}
    counts: dict[str, int] = {}
    for cid, o in outcomes.items():
        if not o.by_building:
            continue
        w = specs[cid].weight
        for building, bf in o.by_building.items():
            if building == "__null__":
                continue
            checked, failed = bf["checked"], bf["failed"]
            rate = 1.0 if checked <= 0 else max(0.0, 1.0 - failed / checked)
            by_b.setdefault(building, []).append((w, rate))
            counts[building] = counts.get(building, 0) + 1
    return {b: (_weighted(v), counts[b]) for b, v in by_b.items()}
