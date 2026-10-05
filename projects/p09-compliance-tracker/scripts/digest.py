#!/usr/bin/env python3
"""Weekly compliance digest — renders HTML to stdout/Mailpit (P09).

Usage:
  python scripts/digest.py [--out FILE] [--as-of YYYY-MM-DD]

Reads gold tables (warehouse.duckdb or data/gold). Golden-file test:
  python scripts/digest.py --as-of 2026-03-31 > /tmp/digest.html
  diff /tmp/digest.html tests/golden/digest_2026-03-31.html
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from compliance import status_for, days_overdue, AS_OF


TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Weekly Compliance Digest — {{ as_of }}</title>
<style>
body {font-family: Arial, sans-serif; margin: 20px; color: #1a1a1a;}
h1 {color: #1B4F72;}
h2 {color: #117A65; border-bottom: 1px solid #ccc; padding-bottom: 4px;}
table {border-collapse: collapse; width: 100%; margin-bottom: 20px;}
th, td {border: 1px solid #ddd; padding: 6px; text-align: left; font-size: 13px;}
th {background: #f0f0f0;}
.red {background: #ffcccc;} .amber {background: #fff3cd;} .green {background: #d4edda;}
.footer {font-size: 11px; color: #666; margin-top: 30px;}
</style>
</head>
<body>
<h1>Weekly Compliance Digest — {{ as_of }}</h1>
<p>Synthetic data for portfolio demonstration.</p>

<h2>Overdue ({{ overdue|length }})</h2>
{% if overdue %}
<table>
<tr><th>Inspection</th><th>Building</th><th>Type</th><th>Due</th><th>Days overdue</th><th>Result</th><th>Remedial</th></tr>
{% for r in overdue %}
<tr class="red">
<td>{{ r.inspection_id }}</td><td>{{ r.building_id }}</td><td>{{ r.inspection_name }}</td>
<td>{{ r.due_date }}</td><td>{{ r.days_overdue }}</td><td>{{ r.result }}</td>
<td>{% if r.remedial_opened %}Open ({{ r.remedial_ageing }}d){% else %}—{% endif %}</td>
</tr>
{% endfor %}
</table>
{% else %}<p>None.</p>{% endif %}

<h2>Due within 30 days ({{ due_soon|length }})</h2>
{% if due_soon %}
<table>
<tr><th>Inspection</th><th>Building</th><th>Type</th><th>Due</th><th>Days left</th></tr>
{% for r in due_soon %}
<tr class="amber">
<td>{{ r.inspection_id }}</td><td>{{ r.building_id }}</td><td>{{ r.inspection_name }}</td>
<td>{{ r.due_date }}</td><td>{{ (r.due_date - as_of).days }}</td>
</tr>
{% endfor %}
</table>
{% else %}<p>None.</p>{% endif %}

<h2>Remedial ageing ({{ remedial|length }})</h2>
{% if remedial %}
<table>
<tr><th>Remedial</th><th>Building</th><th>Opened</th><th>Closed</th><th>Ageing (days)</th><th>Contractor</th></tr>
{% for r in remedial %}
<tr class="{% if r.ageing_days is not none and r.ageing_days > 90 %}red{% elif r.ageing_days is not none and r.ageing_days > 30 %}amber{% else %}green{% endif %}">
<td>{{ r.remedial_id }}</td><td>{{ r.building_id }}</td><td>{{ r.opened_date }}</td>
<td>{{ r.closed_date or '—' }}</td><td>{{ r.ageing_days or '—' }}</td><td>{{ r.contractor }}</td>
</tr>
{% endfor %}
</table>
{% else %}<p>None.</p>{% endif %}

<p class="footer">Generated {{ generated }} UTC | Synthetic data for portfolio demonstration.</p>
</body>
</html>
"""


def load_data(as_of: date) -> tuple:
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    # All inspections with status
    sql = """
    SELECT
        f.inspection_id, f.building_id, f.inspection_type_id,
        i.inspection_name, f.due_date, f.completed_date, f.result,
        r.opened_date AS remedial_opened, r.closed_date AS remedial_closed,
        r.remedial_id, r.contractor
    FROM main.fct_inspection AS f
    JOIN main.dim_inspection_type AS i USING (inspection_type_id)
    LEFT JOIN read_parquet('data/gold/remedial_actions.parquet') AS r
        ON r.inspection_id = f.inspection_id
    ORDER BY f.due_date
    """
    rows = con.execute(sql).fetchall()
    cols = [d[0] for d in con.description]
    return rows, cols


def classify(rows, cols, as_of: date):
    overdue = []
    due_soon = []
    remedial = []

    for row in rows:
        d = dict(zip(cols, row))
        due = d["due_date"]
        comp = d["completed_date"]
        res = d["result"]
        has_open = d["remedial_opened"] is not None and d["remedial_closed"] is None

        st = status_for(due_date=due, completed_date=comp, result=res, has_open_remedial=has_open, as_of=as_of)

        if due is not None:
            do = days_overdue(due, as_of)
        else:
            do = None

        if st.value in ("Overdue", "Failed – remedial open"):
            overdue.append(
                {
                    **d,
                    "status": st.value,
                    "days_overdue": do,
                }
            )
        elif st.value == "Due within 30 days":
            due_soon.append({**d, "days_left": (due - as_of).days})

        # Remedial rows (dedup by remedial_id)
        if d["remedial_id"] is not None:
            opened = d["remedial_opened"]
            closed = d["remedial_closed"]
            if opened is not None:
                end = closed if closed is not None else as_of
                ageing = (end - opened).days
            else:
                ageing = None
            remedial.append(
                {
                    "remedial_id": d["remedial_id"],
                    "building_id": d["building_id"],
                    "opened_date": opened,
                    "closed_date": closed,
                    "ageing_days": ageing,
                    "contractor": d["contractor"],
                }
            )

    # Dedup remedial
    seen = set()
    rem = []
    for r in remedial:
        if r["remedial_id"] not in seen:
            seen.add(r["remedial_id"])
            rem.append(r)

    return overdue, due_soon, rem


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Weekly compliance digest (HTML).")
    p.add_argument("--out", default="", help="Write to file (default: stdout)")
    p.add_argument("--as-of", default=AS_OF.isoformat(), help="As-of date (YYYY-MM-DD)")
    args = p.parse_args(argv)

    as_of = date.fromisoformat(args.as_of)
    rows, cols = load_data(as_of)
    overdue, due_soon, remedial = classify(rows, cols, as_of)

    from jinja2 import Template

    tmpl = Template(TEMPLATE)
    html = tmpl.render(
        as_of=as_of.isoformat(),
        overdue=overdue,
        due_soon=due_soon,
        remedial=remedial,
        generated=datetime.now(timezone.utc).isoformat(),
    )

    if args.out:
        Path(args.out).write_text(html, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))