"""Generate synthetic remedial_actions table from Fail results (P09 enrichment).

Planted findings per spec:
- 2 failed inspections with remedial > 90 days
- Seeded from fct_inspection Fail rows; deterministic on seed.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb

AS_OF = date(2026, 3, 31)


def main(out: str = "data/gold/remedial_actions.parquet") -> int:
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    # Pull all Fail inspections
    fails = con.execute(
        """
        SELECT inspection_id, building_id, inspection_type_id, due_date, completed_date
        FROM main.fct_inspection
        WHERE result = 'Fail'
        ORDER BY due_date
        """
    ).fetchall()

    print(f"Fail inspections: {len(fails)}")

    rows = []
    for i, (insp_id, bldg, itype, due, completed) in enumerate(fails):
        # deterministic: first two gets long ageing (>90 days), rest shorter
        if i < 2:
            opened = due + timedelta(days=5)
            closed = None  # still open
            # ensure >90 days ageing from opened to AS_OF
            if (AS_OF - opened).days <= 90:
                opened = AS_OF - timedelta(days=120)
        else:
            opened = due + timedelta(days=5)
            closed = opened + timedelta(days=30)  # resolved in 30 days

        rows.append(
            {
                "inspection_id": insp_id,
                "remedial_id": f"REM-{insp_id[-6:]}",
                "building_id": bldg,
                "inspection_type_id": itype,
                "opened_date": opened,
                "closed_date": closed,
                "description": f"Remedial for {insp_id} ({itype}) at {bldg}",
                "contractor": "Alpha Compliance Ltd" if i % 2 == 0 else "Beta Safety Services",
                "estimated_cost_gbp": 1500 + i * 500,
            }
        )

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    df = pd.DataFrame(rows)
    con2 = duckdb.connect()
    con2.execute(f"COPY df TO '{out_path}' (FORMAT PARQUET)")
    print(f"wrote {len(rows)} remedial actions to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))