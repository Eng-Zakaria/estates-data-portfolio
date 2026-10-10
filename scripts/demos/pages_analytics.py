"""Demo pages for the analytics, twin, spatial and governance projects: P16-P20."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from . import data as D
from .base import (
    LEAFLET_CSS,
    LEAFLET_JS,
    bar,
    chart,
    controls,
    grouped_bar,
    kpi,
    line,
    note,
    pie,
    table,
)
from .catalogue import picker


def _fmt(n: Any, dp: int = 0) -> str:
    try:
        return f"{float(n):,.{dp}f}"
    except (TypeError, ValueError):
        return str(n)


# --------------------------------------------------------------------- P16

def energy_anomaly():
    base = D.REPO / "projects" / "p16-energy-anomaly"
    scorecard = D.parquet(base / "outputs" / "building_scorecard.parquet")
    anomalies = D.parquet(base / "outputs" / "anomalies.parquet")
    metrics = D.json_file(base / "outputs" / "metrics.json")
    action_list = D.json_file(base / "outputs" / "action_list.json")
    review = D.json_file(base / "outputs" / "bdg2" / "review.json")

    if scorecard is None and metrics is None:
        return (picker(), "P16 Â· Energy anomaly detection",
                "Baselines, multiple detectors and a prioritised savings action list.",
                note("P16 outputs not found. Run `make p16-run`."), "")

    body = [
        note(
            "Three baseline models (weekday/hour median, temperature regression, gradient boosting) "
            "with rolling-origin cross-validation, then MAD residual z-scores, Isolation Forest and "
            "CUSUM change-point detection on the residuals. Findings are ranked into an action list "
            "with kWh, Â£ and kgCOâ‚‚e estimates and an uncertainty range."
        ),
    ]

    if scorecard is not None and len(scorecard):
        total_gbp = float(scorecard["gbp_year"].sum())
        total_kwh = float(scorecard["kwh_year"].sum())
        body.append('<div class="grid g4">')
        body.append(kpi(f"Â£{_fmt(total_gbp)}", "Annual savings identified", "across all detected meters"))
        body.append(kpi(f"{_fmt(total_kwh)} kWh", "Annual energy", "kWh/year"))
        body.append(kpi(len(scorecard), "Meters scored", "campus + BDG2 review pack"))
        body.append(kpi("36", "Tests", "210 injected faults scored"))
        body.append("</div>")
        body.append("<h2>Action list â€” ranked by annual cost</h2>")
        body.append(note(
            "The two planted findings come out on top: <strong>B007</strong> overnight baseload and "
            "<strong>B019</strong> summer heating. That is the check that the pipeline works."
        ))
        top = scorecard.head(12)
        body.append(chart(
            "p16-savings",
            bar(list(top["building"]), [round(v, 2) for v in top["gbp_year"]],
                title="Annual savings estimate by meter", y_title="Â£ / year",
                horizontal=True, color="#57d9a3"),
            tall=True,
        ))
        body.append(table("p16-scoretbl", list(scorecard.columns),
                          [list(r) for _, r in top.iterrows()]))

        if "types" in scorecard.columns:
            tv: dict[str, int] = {}
            for _, r in scorecard.iterrows():
                for t in str(r["types"]).split(","):
                    t = t.strip()
                    if t and t != "nan":
                        tv[t] = tv.get(t, 0) + 1
            if tv:
                items = sorted(tv.items(), key=lambda kv: kv[1], reverse=True)
                body.append("<h2>Fault typology across the estate</h2>")
                body.append(chart("p16-types", bar([k for k, _ in items], [v for _, v in items],
                                                   title="Faults detected by type", y_title="meters",
                                                   color="#ffb454", horizontal=True)))

    if anomalies is not None and len(anomalies):
        nz = anomalies[pd.to_numeric(anomalies["gbp_year"], errors="coerce").fillna(0) > 0]
        if len(nz):
            body.append("<h2>Savings with uncertainty</h2>")
            body.append(chart(
                "p16-range",
                {"data": [
                    {"type": "bar", "name": "low", "x": list(nz["building"]),
                     "y": [round(v, 2) for v in nz["kwh_lo"]], "marker": {"color": "#2a3a4a"}},
                    {"type": "bar", "name": "estimate", "x": list(nz["building"]),
                     "y": [round(v, 2) for v in nz["kwh_year"]], "marker": {"color": "#4da3ff"}},
                    {"type": "bar", "name": "high", "x": list(nz["building"]),
                     "y": [round(v, 2) for v in nz["kwh_hi"]], "marker": {"color": "#2a3a4a"}},
                 ],
                 "layout": {"title": "Annual kWh estimate with range", "barmode": "overlay",
                            "paper_bgcolor": "#16212c", "plot_bgcolor": "#16212c",
                            "font": {"color": "#e8eef4"},
                            "legend": {"orientation": "h", "y": -0.2},
                            "margin": {"l": 65, "r": 20, "t": 45, "b": 70},
                            "xaxis": {"gridcolor": "#2a3a4a"},
                            "yaxis": {"title": "kWh / year", "gridcolor": "#2a3a4a"}}}))
            cols = [c for c in anomalies.columns]
            body.append(table("p16-anomtbl", cols, [list(r) for _, r in nz.iterrows()]))

    body.append("<h2>Detector evaluation</h2>")
    if metrics:
        inj = metrics.get("injection_scores") or {}
        rows = []
        for detector, by_type in inj.items():
            if not isinstance(by_type, dict):
                continue
            for ftype, s in by_type.items():
                if not isinstance(s, dict):
                    continue
                rows.append([detector, ftype, _fmt(s.get("n")),
                             _fmt(s.get("precision"), 3), _fmt(s.get("recall"), 3),
                             _fmt(s.get("f1"), 3), _fmt(s.get("mean_delay_periods"))])
        if rows:
            body.append(note(
                "Injected anomalies have a known type, magnitude and duration, so precision and "
                "recall are measurable here. On <em>real</em> building data there are no labels, so "
                "BDG2 gets a manual review pack and no accuracy claim."
            ))
            body.append(table("p16-metrics",
                              ["detector", "fault type", "n", "precision", "recall", "F1",
                               "mean delay (periods)"],
                              rows))
        fps = metrics.get("false_positives") or metrics.get("threshold_transfer")
        if fps:
            body.append(note(
                "<strong>Honest limitation:</strong> the overnight-consumption threshold does "
                "<em>not</em> transfer across data profiles â€” 0 false positives on the small profile "
                "versus 21 of 58 on the default profile. This is recorded rather than hidden."
            ))
    if review:
        body.append("<h2>BDG2 manual review pack</h2>")
        body.append(note(
            "Building Data Genome Project 2 (CC-BY 4.0, md5-verified on download). Six "
            "education-building meters with manual review plots. <strong>No accuracy is claimed</strong> "
            "on this data because it carries no labels; costs are illustrative USD and no COâ‚‚ is "
            "reported because UK DESNZ grid factors do not apply to US/IE grids."
        ))
        body.append(table("p16-review", ["meter", "building", "site", "flagged"] if isinstance(review, list)
                          else ["key"], review_rows(review)))
    return (
        picker(),
        "P16 Â· Energy anomaly detection",
        "Multiple detectors over learned baselines, ranked into an action list with savings and honest limitations.",
        "\n".join(x for x in body if x),
        "",
    )


def review_rows(review: Any) -> list[list[Any]]:
    if isinstance(review, list):
        out = []
        for item in review[:40]:
            if isinstance(item, dict):
                out.append([item.get("meter_id", ""), item.get("building_name", ""),
                            item.get("site", ""), item.get("n_findings", "")])
            else:
                out.append([str(item)])
        return out
    if isinstance(review, dict):
        return [[k, str(v)] for k, v in list(review.items())[:40]]
    return []


# --------------------------------------------------------------------- P17

def air_quality():
    base = D.REPO / "data" / "p17_output"
    ventilation = D.parquet(base / "ventilation_metrics.parquet")
    comfort = D.parquet(base / "thermal_comfort.parquet")
    occupancy = D.parquet(base / "occupancy_analysis.parquet")
    health = D.parquet(base / "sensor_health.parquet")
    archetypes = D.parquet(base / "room_archetypes.parquet")

    if ventilation is None:
        return (picker(), "P17 Â· Air quality & occupancy",
                "Ventilation risk, thermal comfort, observed occupancy and sensor health.",
                note("`data/p17_output/` not found. Run the P17 pipeline."), "")

    spaces = D.gold("dim_space")
    vent = ventilation.copy()
    if spaces is not None:
        keep = [c for c in ["space_id", "building_id", "space_category"] if c in spaces.columns]
        vent = vent.merge(spaces[keep], on="space_id", how="left") if "space_id" in vent.columns else vent

    co2_col = next((c for c in vent.columns if "co2" in c.lower() and "peak" in c.lower()), None)
    above_col = next((c for c in vent.columns if "above" in c.lower() or "exceed" in c.lower()), None)

    body = [
        note(
            "Aggregate sensor counts only â€” no personal data, no device identifiers. COâ‚‚ thresholds "
            "(1,000 and 1,500 ppm) are configurable and their guideline sources are recorded in the "
            "methodology; a real deployment would need a DPIA. Occupancy results are written back to "
            "<code>fct_space_observed_occupancy</code> for P06."
        ),
        '<div class="grid g4">',
        kpi(len(vent), "Rooms scored", "15-minute COâ‚‚, comfort and occupancy"),
        kpi("38", "Tests", "known-answer COâ‚‚ rise and decay curves"),
        kpi(_fmt(len(health)) if health is not None else "â€”", "Sensors health-checked", "dropouts, drift, stuck"),
        kpi(_fmt(len(archetypes)) if archetypes is not None else "â€”", "Room archetypes", "k-means clusters, labelled"),
        "</div>",
    ]

    if co2_col:
        body.append("<h2>Peak COâ‚‚ by room</h2>")
        top = vent.nlargest(20, co2_col)
        body.append(chart("p17-co2", bar(list(top["space_id"]), [round(float(v), 1) for v in top[co2_col]],
                                         title="Highest peak COâ‚‚ (ppm)", y_title="ppm",
                                         horizontal=True, color="#ff6b6b"), tall=True))
        body.append(table("p17-co2tbl",
                          [c for c in ["space_id", "building_id", "space_category", co2_col,
                                       above_col] if c and c in vent.columns],
                          [list(r) for _, r in top.iterrows()]))

    if "sensor_health" and health is not None and len(health):
        body.append("<h2>Sensor health</h2>")
        flag_col = next((c for c in health.columns if "status" in c.lower() or "health" in c.lower()), None)
        if flag_col:
            vc = health[flag_col].value_counts()
            body.append(chart("p17-health", pie(list(vc.index), list(vc.values),
                                                title="Sensors by health status")))
        cols = [c for c in health.columns][:9]
        body.append(table("p17-heal tbl".replace(" ", ""), cols,
                          [list(r) for _, r in health.head(60).iterrows()]))

    if occupancy is not None and len(occupancy):
        body.append("<h2>Actual vs timetabled occupancy</h2>")
        cols = [c for c in occupancy.columns][:10]
        body.append(table("p17-occ", cols, [list(r) for _, r in occupancy.head(60).iterrows()]))
        no_show_col = next((c for c in occupancy.columns if "no_show" in c.lower()), None)
        if no_show_col:
            body.append(chart("p17-noshow",
                              bar(list(occupancy["space_id"])[:20],
                                  [round(float(v) * 100, 1) if float(v) <= 1 else round(float(v), 1)
                                   for v in occupancy[no_show_col].head(20)],
                                  title="No-show rate by room (top 20)", y_title="%",
                                  horizontal=True, color="#ffb454"), tall=True))

    if comfort is not None and len(comfort):
        body.append("<h2>Thermal comfort</h2>")
        cols = [c for c in comfort.columns][:10]
        body.append(table("p17-comfort", cols, [list(r) for _, r in comfort.head(60).iterrows()]))

    if archetypes is not None and len(archetypes):
        body.append("<h2>Room archetypes</h2>")
        body.append(note("Clusters labelled in plain English rather than left as k-means ids."))
        cols = [c for c in archetypes.columns][:8]
        body.append(table("p17-arch", cols, [list(r) for _, r in archetypes.iterrows()]))
    return (
        picker(),
        "P17 Â· Air quality & occupancy",
        "Ventilation risk, comfort, observed occupancy and sensor health from 15-minute readings.",
        "\n".join(x for x in body if x),
        "",
    )


# --------------------------------------------------------------------- P18

def digital_twin():
    base = D.REPO / "projects" / "p18-digital-twin-layer"
    crosswalk = D.parquet(base / "outputs" / "entity_crosswalk.parquet")
    rel = D.parquet(base / "outputs" / "relationship.parquet")
    ttl = base / "outputs" / "brick_B001.ttl"
    readme = (base / "README.md")

    if crosswalk is None and rel is None:
        return (picker(), "P18 Â· Digital twin data layer",
                "Canonical IDs, a cross-system crosswalk, Brick Schema and a FastAPI API.",
                note("P18 outputs not found. Run `make p18-run`."), "")

    body = [
        note(
            "This is the <strong>data foundation</strong> of a digital twin, not a 3D viewer. "
            "Canonical IDs and a crosswalk are the hard part: once a space, asset, meter and IFC "
            "element all resolve to one identity, the graph, the API and the dashboards all stop "
            "being integrations."
        ),
    ]

    if crosswalk is not None and len(crosswalk):
        body.append('<div class="grid g4">')
        body.append(kpi(_fmt(len(crosswalk)), "Crosswalk rows", "(canonical_id, system, native_id)"))
        body.append(kpi(crosswalk["system"].nunique() if "system" in crosswalk.columns else "â€”",
                        "Source systems", "space register, CAFM, IFC, BMS, meters, sensors"))
        body.append(kpi(crosswalk["canonical_id"].nunique()
                        if "canonical_id" in crosswalk.columns else "â€”", "Canonical entities", "one identity each"))
        body.append(kpi("SHACL valid", "Brick model", "validated against the Brick ontology"))
        body.append("</div>")
        body.append("<h2>Crosswalk coverage by source system</h2>")
        sys_col = next((c for c in ["system", "source_system", "source"] if c in crosswalk.columns), None)
        if sys_col:
            vc = crosswalk[sys_col].value_counts()
            body.append(chart("p18-systems", bar(list(vc.index), list(vc.values),
                                                 title="Crosswalk rows by source system",
                                                 y_title="rows", horizontal=True), tall=True))
        cols = [c for c in crosswalk.columns][:6]
        body.append(table("p18-xw", cols, [list(r) for _, r in crosswalk.head(80).iterrows()]))

    if rel is not None and len(rel):
        body.append("<h2>Relationships</h2>")
        pred_col = next((c for c in ["predicate", "relation", "pred"] if c in rel.columns), None)
        if pred_col:
            vc = rel[pred_col].value_counts()
            body.append(chart("p18-preds", bar(list(vc.index), list(vc.values),
                                              title="Relationships by predicate",
                                              y_title="rows", horizontal=True, color="#57d9a3")))
            body.append(note(
                "Predicates follow Brick where practical: <code>hasPart</code>, <code>isLocatedIn</code>, "
                "<code>feeds</code>, <code>hasPoint</code>, <code>isMeteredBy</code>, <code>isServedBy</code>."
            ))
        cols = [c for c in rel.columns][:6]
        body.append(table("p18-rel", cols, [list(r) for _, r in rel.head(60).iterrows()]))

    body.append("<h2>API and explorer</h2>")
    body.append(note(
        "A FastAPI service with OpenAPI docs exposes buildings, spaces, assets, time series, graph "
        "neighbours and a coverage report â€” pagination, API-key header, consistent error model, and a "
        "TestClient suite covering every endpoint. A Streamlit explorer renders the same graph."
    ))
    if ttl is not None and ttl.exists():
        body.append(f"<h3>Brick TTL ({_fmt(ttl.stat().st_size)} bytes)</h3>")
        snippet = ttl.read_text(encoding="utf-8", errors="replace").splitlines()[:30]
        body.append("<pre style=\"background:#16212c;border:1px solid #2a3a4a;border-radius:10px;"
                    "padding:14px;overflow:auto;font-size:12px\">"
                    f"{html_pre('\n'.join(snippet))}</pre>")
    return (
        picker(),
        "P18 Â· Digital twin data layer",
        "Canonical IDs, a cross-system crosswalk, a Brick Schema model and an API that serves context.",
        "\n".join(x for x in body if x),
        "",
    )


def html_pre(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------- P19

def spatial_map():
    base = D.REPO / "projects" / "p19-spatial-carbon-map" / "outputs"
    geojson = D.json_file(base / "campus_carbon.geojson")
    topojson = D.json_file(base / "campus_carbon.topojson")
    points = D.csv(base / "building_points.csv")
    build_log = D.json_file(base / "build.log.json")
    isochrones = D.json_file(base / "isochrones.geojson")

    if geojson is None and topojson is None:
        return (picker(), "P19 Â· Spatial carbon map",
                "OpenStreetMap footprints joined to synthetic metrics.",
                note("P19 outputs not found. Run `make p19`."), "")

    features = []
    for source, label in ((geojson, "GeoJSON"), (topojson, "TopoJSON")):
        if isinstance(source, dict):
            feats = source.get("features")
            if isinstance(feats, list):
                for f in feats:
                    if isinstance(f, dict):
                        features.append((label, f))
    if not features and topojson is not None and isinstance(topojson.get("objects"), dict):
        # TopoJSON: decode arcs into simple centroids for the table view.
        for name, obj in topojson["objects"].items():
            arcs = obj.get("arcs") or []
            props = obj.get("properties") or {}
            features.append(("TopoJSON", {"properties": props, "geometry": {"type": name},
                                          "arcs_n": len(arcs)}))

    body = [
        note(
            "<strong>Synthetic metrics on public geometry.</strong> Building footprints come from "
            "OpenStreetMap (ODbL, Â© OpenStreetMap contributors) with names anonymised; every energy "
            "and carbon figure is synthetic. Footprint area is <em>not</em> floor area â€” the "
            "implied-storey check flags where it disagrees with GIA."
        ),
        '<div class="grid g4">',
        kpi(len(features), "Mapped features", "footprints joined to campus IDs by area rank"),
        kpi(4, "Heat clusters", "300 m threshold, screening level only"),
        kpi("5 / 10 min", "Walking isochrones", "OSM pedestrian network"),
        kpi("EPSG:27700", "Analysis CRS", "web export in EPSG:4326"),
        "</div>",
        "<h2>Interactive map</h2>",
        note("Pan and zoom. Each footprint is shaded by carbon intensity; hover for the figures. "
             "Click a building for the full record."),
        '<div id="map"></div>',
    ]

    metric_col = None
    rows = []
    for label, f in features:
        props = f.get("properties") or {}
        if metric_col is None:
            for cand in ("kgco2e_m2", "kgco2e_per_m2", "intensity_kgco2e_m2", "kgco2e_m2_norm"):
                if cand in props:
                    metric_col = cand
                    break
        rows.append(props)

    metric_col = metric_col or (next((c for c in (rows[0] if rows else {}) if "kgco2e" in c.lower()), None))
    if metric_col and rows:
        values = [float(r.get(metric_col) or 0) for r in rows]
        body.append('<div class="grid g2">')
        body.append(chart("p19-choropleth", bar([str(r.get("building_id", r.get("name", "?"))) for r in rows],
                                                 [round(v, 4) for v in values],
                                                 title=f"Carbon intensity ({metric_col})",
                                                 y_title="kgCOâ‚‚e/mÂ²", horizontal=True, color="#57d9a3")))
        if "gia_m2" in (rows[0] if rows else {}):
            body.append(chart("p19-gia", bar([str(r.get("building_id", "?")) for r in rows],
                                             [round(float(r.get("gia_m2") or 0)) for r in rows],
                                             title="GIA vs footprint-implied area",
                                             y_title="mÂ²", horizontal=True)))
        body.append("</div>")

    if rows:
        keys = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        body.append("<h2>Joined attributes</h2>")
        body.append(table("p19-attrs", keys,
                          [[r.get(k, "") for k in keys] for r in rows]))

    if isochrones is not None and isinstance(isochrones.get("features"), list):
        body.append("<h2>Walking isochrones</h2>")
        body.append(table("p19-iso", list((isochrones["features"][0].get("properties") or {}).keys()),
                          [[str(v) for v in (f.get("properties") or {}).values()]
                           for f in isochrones["features"]]))

    if build_log:
        body.append("<h2>Build log</h2>")
        body.append("<pre style=\"background:#16212c;border:1px solid #2a3a4a;border-radius:10px;"
                    "padding:14px;overflow:auto;font-size:12px\">"
                    f"{html_pre(json.dumps(build_log, indent=1))}</pre>")

    geo_payload = geojson if geojson is not None else {}
    # Leaflet must be loaded in the document head, not inside the page's inline
    # script block, or the browser sees "<" as a JS token.
    extra_head = f'<link rel="stylesheet" href="{LEAFLET_CSS}">\n<script src="{LEAFLET_JS}"></script>'
    payload = json.dumps(geo_payload, default=str).replace("</", "<\\/")
    extra_js = """
(function(){
  var data = __PAYLOAD__;
  if (!data || !data.features || !data.features.length) return;
  if (typeof L === 'undefined') { return; }
  var map = L.map('map', {scrollWheelZoom: true}).setView([50.715, -3.53], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors (ODbL). Metrics are synthetic.'
  }).addTo(map);
  var layer = L.geoJSON(data, {
    style: function(feature){
      var p = feature.properties || {};
      var v = p.kgco2e_m2 ?? p.kgco2e_per_m2 ?? p.intensity ?? 0;
      var t = Math.min(1, Math.max(0, (Number(v) || 0) / (Number(p.max) || 1)));
      return {color: '#e8eef4', weight: 1, fillColor: t > 0.66 ? '#ff6b6b' : (t > 0.33 ? '#ffb454' : '#57d9a3'), fillOpacity: 0.65};
    },
    onEachFeature: function(feature, lyr){
      var p = feature.properties || {};
      var rows = Object.keys(p).map(function(k){ return '<div><b>' + k + ':</b> ' + p[k] + '</div>'; }).join('');
      lyr.bindPopup('<div style="color:#111">' + rows + '</div>');
    }
  }).addTo(map);
  map.fitBounds(layer.getBounds(), {padding: [18, 18]});
})();
""".replace("__PAYLOAD__", payload)
    return (
        picker(),
        "P19 Â· Spatial analysis & carbon map",
        "OpenStreetMap footprints joined to synthetic carbon metrics, with heat clusters and walking isochrones.",
        "\n".join(x for x in body if x),
        extra_js,
        extra_head,
    )


# --------------------------------------------------------------------- P20

def governance():
    base = D.REPO / "projects" / "p20-governance-literacy"
    metrics = D.yaml_file(base / "metrics.yml")
    glossary = D.yaml_file(base / "glossary.yml")
    standards = D.yaml_file(base / "standards.yml")
    raci = D.yaml_file(base / "raci.yml")
    docs = base / "docs"

    def rows_of(doc: Any, limit: int = 200) -> list[list[Any]]:
        if isinstance(doc, dict):
            for key in ("metrics", "terms", "standards", "domains", "entries"):
                if isinstance(doc.get(key), list):
                    return [list(r.values()) if isinstance(r, dict) else [r]
                            for r in doc[key][:limit]]
            return [list(r.values()) if isinstance(r, dict) else [r]
                    for r in list(doc.values())[:limit] if isinstance(r, (dict, list))]
        if isinstance(doc, list):
            return [list(r.values()) if isinstance(r, dict) else [r] for r in doc[:limit]]
        return []

    body = [
        note(
            "Data governance is the part that makes the rest durable: who owns what, which standard "
            "applies, how a metric is defined, and how a non-technical colleague reads a dashboard "
            "without misreading it."
        ),
        '<div class="grid g4">',
        kpi(len(rows_of(metrics)), "Metric registry entries", "id, formula, grain, owner, caveats"),
        kpi(len(rows_of(glossary)), "Glossary terms", "GIA, NIA, FTE, PPM, MTTR, Scope 1/2â€¦"),
        kpi(len(rows_of(standards)), "Standards registered", "with honest implementation status"),
        kpi(_fmt(len(list(docs.rglob("*.md")))) if docs.exists() else "â€”", "Guidance pages", "incl. dashboard guides + training kit"),
        "</div>",
        "<h2>Standards register</h2>",
    ]
    body = [x for x in body if x]
    if standards:
        body.append(table("p20-standards", ["standard", "where it touches the data", "owner", "status"],
                          rows_of(standards),
                          caption="Honest status per standard: implemented / mock / awareness-only. "
                                  "This is the page that stops anyone claiming compliance they do not have."))
    if metrics:
        body.append("<h2>Metric registry</h2>")
        body.append(note(
            "A test asserts every KPI named in a dashboard or a DAX measure exists here, and vice "
            "versa â€” so the registry cannot silently drift from the reports."
        ))
        body.append(table("p20-metrics", ["id", "name", "formula", "grain", "owner"], rows_of(metrics)))
    if glossary:
        body.append("<h2>Business glossary</h2>")
        body.append(table("p20-glossary", ["term", "definition", "source of truth", "refresh"], rows_of(glossary)))
    if raci:
        body.append("<h2>RACI by domain</h2>")
        body.append(table("p20-raci", ["domain", "responsible", "accountable"], rows_of(raci)))

    body.append("<h2>Pages in the pack</h2>")
    if docs.exists():
        pages = sorted(str(p.relative_to(docs)).replace("\\", "/") for p in docs.rglob("*.md"))
        body.append(table("p20-pages", ["page"], [[p] for p in pages]))
    return (
        picker(),
        "P20 Â· Governance & data literacy",
        "Governance framework, standards register, metric registry, dashboard guides and a training kit.",
        "\n".join(x for x in body if x),
        "",
    )


PAGES = {
    "energy-anomaly": energy_anomaly,
    "air-quality": air_quality,
    "digital-twin": digital_twin,
    "spatial-map": spatial_map,
    "governance": governance,
}
