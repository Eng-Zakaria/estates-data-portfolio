"""Build DQ scorecard seed from P01 reconciliation (honest snapshot of quarantine rates)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "seeds" / "seed_dq_snapshot.csv"


def main() -> None:
    rep = json.loads(Path("data/lakehouse/reconciliation.json").read_text(encoding="utf-8"))
    rows = []
    for r in rep:
        total = r["silver"] + r["quarantine"] if r.get("grain") == "row" else r.get("silver_plus_q", 0)
        quar = r["quarantine"]
        rows.append(
            {
                "dataset": r["source"],
                "grain": r.get("grain", "row"),
                "rows_checked": total,
                "rows_quarantined": quar,
                "pass_rate": round(1 - quar / total, 4) if total else 1.0,
            }
        )
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"dq snapshot: {len(rows)} datasets -> {OUT}")


if __name__ == "__main__":
    main()
