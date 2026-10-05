"""P05 DQ gate for CI.

Fails (exit 1) if any DQ check with severity=error failed.
P03 (platform/quality) is not built yet: in that case print an explicit
SKIP notice and exit 0, so the missing gate is visible but never silent.
Remove the skip branch when P03 lands.
"""

from __future__ import annotations

import json
from pathlib import Path

QUALITY = Path("platform/quality")
RESULTS = QUALITY / "dq_results.json"


def main() -> int:
    if not QUALITY.is_dir() or not RESULTS.exists():
        print(
            "SKIP: platform/quality DQ results not present (P03 not built yet). "
            "Fail-on-error gate will enforce once P03 lands."
        )
        return 0
    payload = json.loads(RESULTS.read_text(encoding="utf-8-sig"))
    errors = [r for r in payload.get("results", []) if r.get("severity") == "error" and r.get("status") != "pass"]
    if errors:
        print(f"DQ GATE FAILED: {len(errors)} error-severity checks failing:")
        for r in errors[:20]:
            print(f"  - {r.get('dataset')}.{r.get('check_id')}: {r.get('status')}")
        return 1
    print(f"DQ gate passed ({len(payload.get('results', []))} checks, 0 error failures).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
