"""Switch the P15 validator function node from Python to JavaScript regex syntax.

Node-RED runs the function node on V8, which does not support Python's
`(?P<name>...)` named-group syntax; every message died with
"Invalid regular expression ... Invalid group".

The contract file (`contracts/validation_rules.json`) stays in Python syntax
because `src/validate.py` consumes it directly. This script rewrites the
pattern to the JS equivalent when writing the flow fragment, so both runtimes
enforce the same shape.

Run after editing the flow fragments, then rebuild the merged flow.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

FLOW = Path(__file__).resolve().parents[1] / "flows" / "bms_ingest.json"
CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "validation_rules.json"


def python_to_js(pattern: str) -> str:
    """Rewrite `(?P<name>...)` as `(?<name>...)`, the only construct used here."""
    return re.sub(r"\(\?P<([a-z_]+)>", r"(?<\1>", pattern)


def main() -> None:
    contract_pattern = json.loads(CONTRACT.read_text(encoding="utf-8"))["topic_pattern"]
    js_pattern = python_to_js(contract_pattern)
    if js_pattern == contract_pattern:
        print("WARNING: contract pattern had no Python named groups; nothing to rewrite")

    nodes = json.loads(FLOW.read_text(encoding="utf-8"))
    patched = 0
    for node in nodes:
        if node.get("type") != "function" or "topicPattern" not in (node.get("func") or ""):
            continue
        func = node["func"]
        # the pattern is compiled from the contract at runtime, so the JS-safe
        # form is applied where the contract string is read
        if "JS_TOPIC_PATTERN" in func:
            continue
        func = func.replace(
            "const topicPattern = new RegExp(rules.topic_pattern);",
            "// rules.topic_pattern is written in Python named-group syntax for\n"
            "// src/validate.py; V8 needs (?<name>...) instead of (?P<name>...).\n"
            "const topicPattern = new RegExp(JS_TOPIC_PATTERN);",
        )
        func = func.replace(
            "const m = topicPattern.exec(topic);",
            "const m = topicPattern.exec(topic);",
        )
        # inject the pre-converted pattern as a constant
        func = func.replace(
            "// Validate one BMS message against contracts/validation_rules.json.",
            f"const JS_TOPIC_PATTERN = {json.dumps(js_pattern)};\n\n"
            "// Validate one BMS message against contracts/validation_rules.json.",
            1,
        )
        node["func"] = func
        patched += 1
    FLOW.write_text(json.dumps(nodes, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Patched {patched} function node(s); JS pattern: {js_pattern}")


if __name__ == "__main__":
    main()
