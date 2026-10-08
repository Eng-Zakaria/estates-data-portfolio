"""Outputs: anomalies.parquet, building_scorecard.parquet, per-building HTML reports.

Evidence plots are dependency-free inline SVG (downsampled to <= 500 points):
raw series polyline, MAD spike markers, flatline spans, change-point rules.
No plotly/matplotlib needed; outputs render anywhere.
"""

from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd
from jinja2 import Template

from .config import OUTPUTS

PAGE = Template(
    """<html><head><title>{{ building }} energy exceptions (SYNTHETIC)</title></head>
<body><h1>{{ building }} — energy exceptions</h1>
<p><em>Synthetic data for portfolio demonstration. No real building performance is implied.</em></p>
<h2>Findings ({{ findings|length }})</h2>
<table border="1"><tr><th>type</th><th>detector</th><th>start</th><th>kWh/day</th>
<th>{{ currency }}/yr</th><th>kgCO2e/yr</th></tr>
{% for f in findings %}<tr><td>{{ f.type }}</td><td>{{ f.detector }}</td><td>{{ f.start }}</td>
<td>{{ f.kwh_day }}</td><td>{{ f.cost_year }}</td><td>{{ f.kgco2e_year }}</td></tr>{% endfor %}</table>
<h2>Notes</h2><p>{{ notes }}</p>
<h2>Evidence</h2><div>{{ plot_html|safe }}</div>
</body></html>"""
)


def svg_series(
    ts: pd.Series,
    values: np.ndarray,
    mad_flags: np.ndarray | None = None,
    flat_flags: np.ndarray | None = None,
    change_points: list[int] | None = None,
    width: int = 640,
    height: int = 180,
    max_points: int = 500,
) -> str:
    """Inline SVG time-series plot. Indices refer to full-resolution positions."""
    v = np.asarray(values, float)
    n = len(v)
    step = max(1, n // max_points)
    idx = np.arange(0, n, step)
    vv = v[idx]
    finite = np.isfinite(vv)
    ymin = float(np.nanmin(vv[finite])) if finite.any() else 0.0
    ymax = float(np.nanmax(vv[finite])) if finite.any() else 1.0
    if ymax - ymin < 1e-9:
        ymax = ymin + 1.0
    x = (idx / max(n - 1, 1) * (width - 8) + 4).tolist()
    y = (height - 8 - (vv - ymin) / (ymax - ymin) * (height - 16)).tolist()
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b, ok in zip(x, y, finite) if ok)
    parts = [
        f"<svg width='{width}' height='{height}' style='border:1px solid #999' role='img'>",
        f"<polyline points='{html.escape(pts)}' fill='none' stroke='#1f77b4' stroke-width='1'/>",
    ]
    if flat_flags is not None:
        fl = np.asarray(flat_flags, dtype=bool)
        # shade flatline spans (merged runs)
        i = 0
        while i < n:
            if fl[i]:
                j = i
                while j + 1 < n and fl[j + 1]:
                    j += 1
                parts.append(
                    f"<rect x='{i / max(n - 1, 1) * (width - 8) + 4:.1f}' y='0' "
                    f"width='{max(2.0, (j - i) / max(n - 1, 1) * (width - 8)):.1f}' "
                    f"height='{height}' fill='#ff7f0e' opacity='0.3'/>"
                )
                i = j + 1
            else:
                i += 1
    if mad_flags is not None:
        for i in np.where(np.asarray(mad_flags, dtype=bool))[0]:
            parts.append(
                f"<circle cx='{i / max(n - 1, 1) * (width - 8) + 4:.1f}' "
                f"cy='{height - 8 - (v[i] - ymin) / (ymax - ymin) * (height - 16):.1f}' "
                f"r='3' fill='#d62728'/>"
            )
    for cp in change_points or []:
        parts.append(
            f"<line x1='{cp / max(n - 1, 1) * (width - 8) + 4:.1f}' y1='0' "
            f"x2='{cp / max(n - 1, 1) * (width - 8) + 4:.1f}' y2='{height}' "
            f"stroke='#2ca02c' stroke-dasharray='4,2'/>"
        )
    try:
        t0, t1 = str(ts.iloc[0]), str(ts.iloc[-1])
    except Exception:
        t0 = t1 = ""
    parts.append(f"<text x='4' y='{height - 1}' font-size='9' fill='#555'>{html.escape(t0)} … {html.escape(t1)}</text>")
    parts.append("</svg>")
    return "".join(parts)


def write_anomalies(rows: list[dict[str, object]], out: Path | None = None) -> Path:
    out = out or (OUTPUTS / "anomalies.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out, index=False)
    return out


def write_scorecard(rows: list[dict[str, object]], out: Path | None = None) -> Path:
    out = out or (OUTPUTS / "building_scorecard.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out, index=False)
    return out


def building_page(
    building: str,
    findings: list[dict[str, object]],
    plot_html: str,
    notes: str,
    out: Path | None = None,
    currency: str = "£",
) -> Path:
    out = out or (OUTPUTS / "reports" / f"{building}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        PAGE.render(building=building, findings=findings, plot_html=plot_html, notes=notes, currency=currency),
        encoding="utf-8",
    )
    return out
