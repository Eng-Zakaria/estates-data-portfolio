"""Static web-demo toolkit.

Renders self-contained HTML pages for GitHub Pages from real, measured data.
No server, no build framework: one HTML file per project, data baked in as JSON,
charts drawn with Plotly and maps with Leaflet from a CDN.

Design rules that matter here:
* Every page states loudly that the data is synthetic.
* Numbers come from the same marts/docs the project READMEs quote, so a
  reviewer can tie any figure on a page back to a test or an acceptance doc.
* If a project's data is missing, the builder says so instead of inventing
  numbers.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

PLOTLY_JS = "https://cdn.plot.ly/plotly-2.35.2.min.js"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"

SYNTHETIC_BANNER = (
    "Synthetic data for portfolio demonstration. No real university, building, "
    "person or performance data is shown or implied."
)

# Shared CSS keeps every page visually identical to the rest of the portfolio.
CSS = """
:root{
  --bg:#0f1720; --panel:#16212c; --panel2:#1d2b38; --line:#2a3a4a;
  --fg:#e8eef4; --muted:#9fb3c8; --accent:#4da3ff; --accent2:#57d9a3;
  --warn:#ffb454; --bad:#ff6b6b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:15px/1.55 ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
header{padding:22px 26px 14px;border-bottom:1px solid var(--line);background:var(--panel)}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:11px;color:var(--accent)}
h1{margin:6px 0 4px;font-size:25px;line-height:1.2}
.sub{color:var(--muted);font-size:14px;max-width:70ch}
.banner{margin:14px 26px 0;padding:10px 14px;border-radius:8px;font-size:13px;
  background:rgba(255,180,84,.12);border:1px solid rgba(255,180,84,.45);color:#ffd9a8}
main{padding:20px 26px 60px}
nav.picker{margin:16px 26px 0;display:flex;flex-wrap:wrap;gap:6px}
nav.picker a{font-size:12px;padding:4px 9px;border:1px solid var(--line);
  border-radius:20px;text-decoration:none;color:var(--muted);background:var(--panel)}
nav.picker a:hover{color:var(--fg);border-color:var(--accent)}
nav.picker a.on{background:var(--accent);color:#04121f;border-color:var(--accent);font-weight:600}
h2{font-size:17px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:14px;margin:18px 0 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.grid{display:grid;gap:14px}
.g2{grid-template-columns:repeat(auto-fit,minmax(380px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.g4{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.kpi .v{font-size:26px;font-weight:650;letter-spacing:-.01em}
.kpi .l{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px}
.kpi .n{color:var(--muted);font-size:12px;margin-top:4px}
.chart{width:100%;height:380px}
.chart.tall{height:520px}
.controls{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:12px 0}
.controls label{display:flex;flex-direction:column;font-size:11px;color:var(--muted);
  text-transform:uppercase;letter-spacing:.07em;gap:4px}
select,input{background:var(--panel2);color:var(--fg);border:1px solid var(--line);
  border-radius:6px;padding:6px 8px;font-size:13px;min-width:150px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:6px 9px;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.07em;position:sticky;top:0;
  background:var(--panel);cursor:pointer}
tbody tr:hover{background:var(--panel2)}
.scroll{max-height:460px;overflow:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.tag{display:inline-block;padding:1px 7px;border-radius:11px;font-size:11px;border:1px solid var(--line)}
.ok{color:var(--accent2);border-color:var(--accent2)}
.warn{color:var(--warn);border-color:var(--warn)}
.bad{color:var(--bad);border-color:var(--bad)}
.note{color:var(--muted);font-size:13px;background:var(--panel);border-left:3px solid var(--accent);
  padding:10px 12px;border-radius:0 8px 8px 0;margin:10px 0}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
#map{height:520px;border-radius:10px;border:1px solid var(--line)}
footer{padding:18px 26px 40px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}
a.ll{color:var(--muted)}
"""


def _js(value: Any) -> str:
    """JSON that is safe to inline inside a <script> block."""
    return (
        json.dumps(value, default=str)
        .replace("</", "<\\/")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


def esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


def kpi(value: Any, label: str, note: str = "") -> str:
    note_html = f'<div class="n">{esc(note)}</div>' if note else ""
    return (
        f'<div class="card kpi"><div class="l">{esc(label)}</div>'
        f'<div class="v">{esc(value)}</div>{note_html}</div>'
    )


def note(text: str) -> str:
    return f'<div class="note">{text}</div>'


def chart(div_id: str, figure: Mapping[str, Any], tall: bool = False) -> str:
    cls = "chart tall" if tall else "chart"
    return (
        f'<div class="card"><div id="{esc(div_id)}" class="{cls}"></div>'
        f'<script>window.__fig["{esc(div_id)}"]={_js(figure)};</script></div>'
    )


def table(
    table_id: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
    caption: str = "",
    limit: int = 400,
) -> str:
    """A sortable, searchable table. Rows are truncated client-side for speed."""
    head = "".join(f"<th>{esc(c)}</th>" for c in columns)
    body = []
    for row in itertools_islice(rows, limit):
        cells = []
        for cell in row:
            if isinstance(cell, tuple):  # (value, css-class)
                cells.append(f'<td><span class="tag {esc(cell[1])}">{esc(cell[0])}</span></td>')
            else:
                cells.append(f"<td>{esc(cell)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    cap = f'<div class="note">{caption}</div>' if caption else ""
    return (
        f"{cap}<div class=\"scroll\"><table id=\"{esc(table_id)}\" class=\"sortable\">"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def itertools_islice(rows: Iterable[Any], limit: int) -> list[Any]:
    out: list[Any] = []
    for i, row in enumerate(rows):
        if i >= limit:
            break
        out.append(row)
    return out


def controls(*items: Mapping[str, Any]) -> str:
    """items: {id, label, options: [(value,label)], default}"""
    parts = []
    for item in items:
        opts = "".join(
            f'<option value="{esc(v)}"{" selected" if v == item.get("default") else ""}>'
            f"{esc(lbl)}</option>"
            for v, lbl in item["options"]
        )
        parts.append(
            f'<label>{esc(item["label"])}'
            f'<select id="{esc(item["id"])}">{opts}</select></label>'
        )
    return f'<div class="controls">{"".join(parts)}</div>'


def page(
    *,
    project_id: str,
    title: str,
    subtitle: str,
    body: str,
    picker: Sequence[tuple[str, str, str]],
    extra_js: str = "",
    extra_head: str = "",
    footer: str = "",
) -> str:
    """Assemble a complete HTML document.

    picker: sequence of (project_id, label, href).
    """
    nav = "".join(
        f'<a href="{esc(href)}" class="{"on" if pid == project_id else ""}">{esc(label)}</a>'
        for pid, label, href in picker
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Estates Data Portfolio</title>
<style>{CSS}</style>
<script src="{PLOTLY_JS}"></script>
{extra_head}
</head>
<body>
<script>window.__fig = window.__fig || {{}};</script>
<header>
  <div class="eyebrow">Estates Data Portfolio · {esc(project_id)}</div>
  <h1>{esc(title)}</h1>
  <div class="sub">{subtitle}</div>
</header>
<div class="banner"><strong>Synthetic data.</strong> {esc(SYNTHETIC_BANNER)}</div>
<nav class="picker">{nav}</nav>
<main>
{body}
</main>
<footer>
  {footer or 'Generated from the same gold marts and acceptance evidence quoted in the project README. '
             'Figures are reproduced exactly as measured; see the repository for tests and SQL that tie them back.'}
  <br>Repository: <code>estates-data-portfolio</code>
</footer>
<script>
// Render every Plotly figure embedded on this page.
for (const [id, fig] of Object.entries(window.__fig || {{}})) {{
  const el = document.getElementById(id);
  if (el && window.Plotly) {{
    el.style.width = '100%';
    Plotly.newPlot(id, fig.data, fig.layout, {{displaylogo:false, responsive:true}});
  }}
}};
// Sortable tables: click a header to sort ascending/descending.
document.querySelectorAll('table.sortable').forEach(function (table) {{
  table.querySelectorAll('th').forEach(function (th, idx) {{
    th.addEventListener('click', function () {{
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      const dir = th.dataset.dir === 'asc' ? -1 : 1;
      th.dataset.dir = dir === 1 ? 'asc' : 'desc';
      rows.sort(function (a, b) {{
        const av = a.cells[idx]?.innerText ?? '';
        const bv = b.cells[idx]?.innerText ?? '';
        const an = parseFloat(av.replace(/[^0-9.\\-]/g, ''));
        const bn = parseFloat(bv.replace(/[^0-9.\\-]/g, ''));
        if (!Number.isNaN(an) && !Number.isNaN(bn)) return (an - bn) * dir;
        return av.localeCompare(bv) * dir;
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  }});
}});
{extra_js}
</script>
</body>
</html>"""


def bar(
    labels: Sequence[Any],
    values: Sequence[Any],
    title: str = "",
    y_title: str = "",
    color: str = "#4da3ff",
    horizontal: bool = False,
) -> dict[str, Any]:
    """Bar chart figure."""
    orientation = "h" if horizontal else "v"
    return {
        "data": [
            {
                "type": "bar",
                "x": list(labels),
                "y": list(values),
                "orientation": orientation,
                "marker": {"color": color},
            }
        ],
        "layout": {
            "title": title,
            "paper_bgcolor": "#16212c",
            "plot_bgcolor": "#16212c",
            "font": {"color": "#e8eef4"},
            "margin": {"l": 60, "r": 20, "t": 45 if title else 20, "b": 60},
            "xaxis": {"title": y_title if not horizontal else "", "gridcolor": "#2a3a4a"},
            "yaxis": {
                "title": y_title if horizontal else "",
                "gridcolor": "#2a3a4a",
                "automargin": True,
            },
        },
    }


def line(
    x: Sequence[Any],
    y: Sequence[Any],
    name: str = "",
    title: str = "",
    y_title: str = "",
    color: str = "#57d9a3",
    fill: bool = False,
) -> dict[str, Any]:
    return {
        "data": [
            {
                "type": "scatter",
                "mode": "lines",
                "x": list(x),
                "y": list(y),
                "name": name,
                "line": {"color": color, "width": 2},
                "fill": "tozeroy" if fill else None,
            }
        ],
        "layout": {
            "title": title,
            "paper_bgcolor": "#16212c",
            "plot_bgcolor": "#16212c",
            "font": {"color": "#e8eef4"},
            "margin": {"l": 65, "r": 20, "t": 45 if title else 20, "b": 60},
            "xaxis": {"gridcolor": "#2a3a4a"},
            "yaxis": {"title": y_title, "gridcolor": "#2a3a4a", "automargin": True},
        },
    }


def pie(labels: Sequence[Any], values: Sequence[Any], title: str = "") -> dict[str, Any]:
    palette = [
        "#4da3ff", "#57d9a3", "#ffb454", "#ff6b6b", "#b98cff", "#4ad6d6", "#f77fb0",
    ]
    return {
        "data": [
            {
                "type": "pie",
                "labels": list(labels),
                "values": list(values),
                "marker": {"colors": palette[: len(labels)]},
                "hole": 0.45,
            }
        ],
        "layout": {
            "title": title,
            "paper_bgcolor": "#16212c",
            "font": {"color": "#e8eef4"},
            "margin": {"l": 20, "r": 20, "t": 45 if title else 20, "b": 20},
        },
    }


def heatmap(z: Sequence[Sequence[Any]], x: Sequence[Any], y: Sequence[Any],
            title: str = "", color_scale: str = "Viridis") -> dict[str, Any]:
    return {
        "data": [
            {
                "type": "heatmap",
                "z": [list(r) for r in z],
                "x": [str(v) for v in x],
                "y": [str(v) for v in y],
                "colorscale": color_scale,
                "hovertemplate": "%{y} %{x}: %{z}<extra></extra>",
            }
        ],
        "layout": {
            "title": title,
            "paper_bgcolor": "#16212c",
            "plot_bgcolor": "#16212c",
            "font": {"color": "#e8eef4"},
            "margin": {"l": 120, "r": 20, "t": 45 if title else 20, "b": 60},
            "xaxis": {"title": "", "gridcolor": "#2a3a4a"},
            "yaxis": {"title": "", "gridcolor": "#2a3a4a", "automargin": True},
        },
    }


def grouped_bar(
    labels: Sequence[Any],
    series: Mapping[str, Sequence[Any]],
    title: str = "",
    y_title: str = "",
) -> dict[str, Any]:
    colors = ["#4da3ff", "#57d9a3", "#ffb454", "#ff6b6b"]
    data = [
        {
            "type": "bar",
            "name": name,
            "x": [str(v) for v in labels],
            "y": list(vals),
            "marker": {"color": colors[i % len(colors)]},
        }
        for i, (name, vals) in enumerate(series.items())
    ]
    return {
        "data": data,
        "layout": {
            "title": title,
            "barmode": "group",
            "paper_bgcolor": "#16212c",
            "plot_bgcolor": "#16212c",
            "font": {"color": "#e8eef4"},
            "legend": {"orientation": "h", "y": -0.2},
            "margin": {"l": 65, "r": 20, "t": 45 if title else 20, "b": 70},
            "xaxis": {"gridcolor": "#2a3a4a"},
            "yaxis": {"title": y_title, "gridcolor": "#2a3a4a", "automargin": True},
        },
    }