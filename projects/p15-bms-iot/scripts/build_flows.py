"""Merge the P15 Node-RED flow fragments into the single file Node-RED loads.

Node-RED takes one flow file per runtime, so `flows/bms_ingest.json` (the ingest
tab) and `flows/bms_registry_seed.json` (the registry seed tab) are combined
into `flows/p15_bms.json`. Keeping the fragments separate makes review easier;
this script is the only place that knows about the merge.

    python scripts/build_flows.py
"""

from __future__ import annotations

import json
from pathlib import Path

FLOWS_DIR = Path(__file__).resolve().parents[1] / "flows"
FRAGMENTS = ["bms_ingest.json", "bms_registry_seed.json"]
OUTPUT = FLOWS_DIR / "p15_bms.json"


def build(fragments: list[str] | None = None, out: Path = OUTPUT) -> tuple[int, list[str]]:
    nodes: list[dict] = []
    seen: set[str] = set()
    for name in fragments or FRAGMENTS:
        path = FLOWS_DIR / name
        for node in json.loads(path.read_text(encoding="utf-8")):
            node_id = node.get("id")
            if node_id in seen:
                # the shared database config node is declared once per fragment
                # so each fragment imports cleanly on its own; keep the first
                if node.get("type") in {"postgreSQLConfig", "postgresdb"}:
                    continue
                raise ValueError(f"duplicate node id {node_id} in {name}")
            seen.add(node_id)
            nodes.append(node)
    out.write_text(json.dumps(nodes, indent=2) + "\n", encoding="utf-8", newline="\n")
    return len(nodes), [n.get("type", "?") for n in nodes]


def main() -> None:
    count, types = build()
    print(f"Wrote {count} nodes to {OUTPUT}")
    from collections import Counter

    for node_type, n in sorted(Counter(types).items()):
        print(f"  {node_type}: {n}")


if __name__ == "__main__":
    main()
