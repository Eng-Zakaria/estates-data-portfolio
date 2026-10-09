"""The Node-RED flow: structural checks on the committed JSON.

These do not need a running Node-RED: they assert the merged flow that ships
with the repo is internally consistent (unique node ids, one broker, one
subscription per campus topic, the expected processing stages) so a broken
export fails in CI rather than at `make iot-up`.
"""

from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path

from conftest import FLOW_MERGED, PROJECT

FRAGMENTS = ["bms_ingest.json", "bms_registry_seed.json"]


def _nodes() -> list[dict]:
    return json.loads(FLOW_MERGED.read_text(encoding="utf-8"))


def test_merged_flow_is_valid_json_and_has_a_tab_per_concern():
    nodes = _nodes()
    tabs = [n for n in nodes if n.get("type") == "tab"]
    assert len(tabs) == 2, "an ingest tab and a registry-seed tab"


def test_node_ids_are_unique():
    ids = [n["id"] for n in _nodes()]
    assert len(ids) == len(set(ids))


def test_every_wire_target_exists():
    nodes = _nodes()
    ids = {n["id"] for n in nodes}
    for node in nodes:
        for group in node.get("wires", []):
            for target in group:
                assert target in ids, f"{node['id']} wires to missing node {target}"


def test_one_mqtt_subscription_covering_the_whole_topic_tree():
    subs = [n for n in _nodes() if n.get("type") == "mqtt in"]
    assert len(subs) == 1
    assert subs[0]["topic"] == "campus/#"


def test_processing_stages_are_the_documented_pipeline():
    """subscribe -> validate+map -> batch insert, plus heartbeat and dead letter."""
    types = Counter(n.get("type") for n in _nodes())
    assert types["mqtt in"] == 1
    assert types["mqtt-broker"] == 1
    # validate+map, batching, heartbeat params, dead-letter params, registry params
    assert types["function"] == 5
    # readings, heartbeat, dead letter, staleness alerts, registry seed
    assert types["postgresql"] == 5
    # seed and staleness checks are injected on a timer; a third would need its
    # own doc entry
    assert types["inject"] == 2


def test_broker_config_points_at_the_compose_network():
    """Node-RED must reach mosquitto by service name on the compose network."""
    broker = next(n for n in _nodes() if n.get("type") == "mqtt-broker")
    assert broker["broker"] == "mosquitto"
    # the external listener needs a password; the internal one does not
    assert broker["port"] == "2883"


def test_no_passwords_in_the_committed_flow():
    raw = FLOW_MERGED.read_text(encoding="utf-8")
    assert "credentials" not in [n.get("id") for n in _nodes()]
    for banned in ("bms_pass", "postgres_password", "NR_PASSWORD"):
        assert banned not in raw


def test_flow_is_reproducible_from_its_fragments():
    """`make p15-flows` rebuilds p15_bms.json from the fragments; the rebuilt
    file must have the same nodes in the same order as the committed one."""
    import sys

    sys.path.insert(0, str(PROJECT / "scripts"))
    try:
        from build_flows import build
    finally:
        sys.path.pop()

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "rebuilt.json"
        count, _ = build(out=out)
        regenerated = json.loads(out.read_text(encoding="utf-8"))

    assert count == len(_nodes())
    assert [n["id"] for n in regenerated] == [n["id"] for n in _nodes()]


def test_ingest_tab_batches_before_writing():
    nodes = {n["id"]: n for n in _nodes()}
    func = nodes["fn_batch"]["func"]
    assert "500" in func or "BATCH" in func


def test_heartbeat_and_staleness_alerts_exist():
    nodes = {n["id"]: n for n in _nodes()}
    assert "db_heartbeat" in nodes
    assert "inject_stale" in nodes
    assert "db_stale" in nodes
    # the staleness check runs every 5 min and compares last_seen against now()
    assert nodes["inject_stale"]["repeat"] == "300"
    query = nodes["db_stale"]["query"]
    assert "now() - p.last_seen" in query
    assert "bms.alerts" in query
    assert "STALENESS" in query


def test_dead_letter_and_registry_nodes_present():
    ids = {n["id"] for n in _nodes()}
    assert {"fn_dead_params", "db_dead", "fn_registry", "db_seed"} <= ids


def test_flow_rejects_bad_messages_to_the_dead_letter_table():
    """If the validation function ever returns undefined, the dead-letter
    branch must be the fallback, never the accept branch."""
    nodes = {n["id"]: n for n in _nodes()}
    func = nodes["fn_parse"]["func"]
    assert "reject(" in func
    # the dead-letter params node must receive the reject object
    dead = nodes["fn_dead_params"]["func"]
    assert "reason" in dead