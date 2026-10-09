"""Drop x/y from the PostgreSQL config node in the P15 flows.

Node-RED 4.0.9 classifies a node in `parseConfig` (@node-red/runtime/lib/flows/util.js)
by checking for `x`/`y` **before** it checks the config-node path:

    if (n.hasOwnProperty('x') && n.hasOwnProperty('y')) {
        if (container) { container.nodes[n.id] = n; }   // flow node
    } else {
        flow.configs[n.id] = n;                          // config node
    }

A config node that also carries `x`/`y` and has no `z` therefore lands in
neither `nodes` nor `configs`, `RED.nodes.getNode('cfg_pg')` returns null, and
every dependent node falls back to a stub pool — surfacing as
"node.config.pgPool.connect is not a function".

Run after editing the flow fragments, then rebuild the merged flow.
"""

from __future__ import annotations

import json
from pathlib import Path

FLOWS = Path(__file__).resolve().parents[1] / "flows"
FRAGMENTS = ["bms_ingest.json", "bms_registry_seed.json"]


def main() -> None:
    for name in FRAGMENTS:
        path = FLOWS / name
        if not path.exists():
            continue
        nodes = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for node in nodes:
            if node.get("type") == "postgreSQLConfig":
                removed = [k for k in ("x", "y") if node.pop(k, None) is not None]
                if removed:
                    changed = True
                    print(f"  {node['id']}: removed {', '.join(removed)}")
        if changed:
            path.write_text(json.dumps(nodes, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"Checked {name}")


if __name__ == "__main__":
    main()
