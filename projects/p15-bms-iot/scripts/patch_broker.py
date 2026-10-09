"""Wire the P15 MQTT broker config node to the internal Mosquitto listener.

Node-RED's core `mqtt-broker` node reads its credentials from Node-RED's
encrypted credential store (`flows_cred.json` / `.config.runtime.json`), which
cannot be committed to a repository. A `credentials` key inside the committed
flow JSON is therefore ignored, so a headless demo stack cannot authenticate
that way.

Resolution (documented in mosquitto.conf and docs/security.md): Mosquitto
exposes two listeners -- 1883 password-protected for the host, and 2883 on the
compose network for Node-RED. This script points the broker node at 2883 and
strips the ineffective inline credentials.
"""

from __future__ import annotations

import json
from pathlib import Path

FLOW = Path(__file__).resolve().parents[1] / "flows" / "bms_ingest.json"

BROKER_HOST = "mosquitto"  # docker-compose service name
BROKER_PORT = "2883"  # compose-network listener (see mosquitto.conf)
CONFIG_ID = "broker_localhost"


def main() -> None:
    nodes = json.loads(FLOW.read_text(encoding="utf-8"))
    for node in nodes:
        if node.get("type") == "mqtt-broker":
            node["id"] = CONFIG_ID
            node["broker"] = BROKER_HOST
            node["port"] = BROKER_PORT
            node["name"] = "BMS broker (mosquitto, internal listener)"
            # inline credentials are ignored by Node-RED 4; drop them so the
            # committed flow carries no password at all
            node.pop("credentials", None)
        elif node.get("type") == "mqtt in":
            # the `broker` field on a subscriber is the config node's ID
            node["broker"] = CONFIG_ID
    FLOW.write_text(json.dumps(nodes, indent=2) + "\n", encoding="utf-8", newline="\n")
    for node in nodes:
        if node.get("type") in {"mqtt-broker", "mqtt in"}:
            print(f"  {node['type']}: broker={node['broker']} port={node.get('port', '-')}")


if __name__ == "__main__":
    main()
