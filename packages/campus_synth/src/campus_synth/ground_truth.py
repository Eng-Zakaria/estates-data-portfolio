"""Ground-truth registry writer."""

from __future__ import annotations

from pathlib import Path

import yaml


def write_ground_truth(gt: dict[str, object], defect_logs: list[dict[str, str]], path: Path) -> Path:
    """Merge planted findings + defect log and write YAML deterministically."""
    payload = dict(gt)
    payload["defects"] = sorted(defect_logs, key=lambda d: (d["table"], d["row_key"], d["type"]))
    payload["notes"] = (
        "Synthetic ground truth. Planted findings are deterministic overrides; "
        "defect log enumerates every injected defect (table, row key, type)."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=True, default_flow_style=False)
    return path
