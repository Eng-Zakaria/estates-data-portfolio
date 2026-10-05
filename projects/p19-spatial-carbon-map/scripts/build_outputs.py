"""Build P19 outputs (run from repo root): `make p19` or this script directly.

Reads OSM cache (scripts/fetch_osm.py) + metrics (warehouse, else gold),
writes GeoPackage/GeoJSON/TopoJSON/PNG/Folium/QML + Power BI map handoff
under projects/p19-spatial-carbon-map/outputs/. All metrics synthetic;
geometry (c) OpenStreetMap contributors, ODbL.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from spatial import (  # noqa: E402
    PROJECTED_CRS,
    WGS84,
    assign_ids_by_area,
    centroid_distance_matrix,
    clean_footprints,
    cluster_totals,
    cluster_within,
    flag_storey_outlier,
    footprint_area_m2,
    hull_of_points,
    implied_storeys,
    quantile_breaks,
    to_projected,
)

OUT = HERE / "outputs"
CACHE = Path("data/reference/osm_buildings.geojson")
GRAPH_CACHE = Path("data/reference/osm_walk.graphml")
WALK_M_PER_MIN = 80.0  # 4.8 km/h screening speed


def load_metrics() -> tuple[dict, dict, dict]:
    """Return (gia, gas_kwh, kgco2e_per_m2) keyed by building_id.

    Prefers the live warehouse, falls back to gold extracts; records source.
    """
    try:
        import duckdb

        con = duckdb.connect("data/warehouse.duckdb", read_only=True)
        gia = dict(con.execute("SELECT building_id, gia_m2 FROM main.dim_building").fetchall())
        gas = dict(
            con.execute(
                "SELECT building_id, SUM(kwh) FROM main.fct_energy_daily WHERE utility = 'gas' GROUP BY 1"
            ).fetchall()
        )
        inten = dict(
            con.execute(
                """SELECT d.building_id,
                     SUM(d.kwh * f.factor_kgco2e_per_kwh) / MAX(b.gia_m2)
                   FROM main.fct_energy_daily d
                   JOIN main.dim_building b USING (building_id)
                   JOIN main.dim_emission_factor f ON f.fuel =
                     CASE d.utility WHEN 'electricity' THEN 'electricity'
                                     WHEN 'gas' THEN 'natural_gas' END
                   GROUP BY 1"""
            ).fetchall()
        )
        con.close()
        print("metrics source: warehouse.duckdb")
        return gia, gas, inten
    except Exception as exc:  # noqa: BLE001 — fallback path is the point
        print(f"warehouse unavailable ({exc}); falling back to data/gold")
        import duckdb

        con = duckdb.connect()
        daily = "read_parquet('data/gold/fct_energy_daily.parquet')"
        bld = "read_parquet('data/gold/dim_building.parquet')"
        fac = "read_parquet('data/gold/dim_emission_factor.parquet')"
        gia = dict(con.execute(f"SELECT building_id, gia_m2 FROM {bld}").fetchall())
        gas = dict(con.execute(f"SELECT building_id, SUM(kwh) FROM {daily} WHERE utility='gas' GROUP BY 1").fetchall())
        inten = dict(
            con.execute(
                f"""SELECT d.building_id, SUM(d.kwh * f.factor_kgco2e_per_kwh) / MAX(b.gia_m2)
                    FROM {daily} d JOIN {bld} b USING (building_id)
                    JOIN {fac} f ON f.fuel = CASE d.utility WHEN 'electricity'
                    THEN 'electricity' WHEN 'gas' THEN 'natural_gas' END GROUP BY 1"""
            ).fetchall()
        )
        return gia, gas, inten


def load_graph(bbox: tuple) -> object:
    if GRAPH_CACHE.exists():
        print(f"graph cache hit: {GRAPH_CACHE}")
        return ox.load_graphml(filepath=str(GRAPH_CACHE))
    print("downloading walk network (cached afterwards) ...")
    G = ox.graph_from_bbox(bbox, network_type="walk")
    ox.save_graphml(G, filepath=str(GRAPH_CACHE))
    return G


def isochrones(G: object, lon: float, lat: float) -> dict[str, object]:
    """5/10-min reachable-area hulls around (lon, lat). Screening-level."""
    orig = ox.distance.nearest_nodes(G, X=[lon], Y=[lat])[0]
    polys: dict[str, object] = {}
    for mins in (5, 10):
        dists = nx.single_source_dijkstra_path_length(G, orig, cutoff=mins * WALK_M_PER_MIN, weight="length")
        nodes = [n for n in dists]
        pts = gpd.GeoDataFrame(
            {"node": nodes},
            geometry=[Point(G.nodes[n]["x"], G.nodes[n]["y"]) for n in nodes],
            crs=WGS84,
        )
        polys[f"{mins}min"] = hull_of_points(to_projected(pts))
    return polys


def write_qml(path: Path, breaks: list[float]) -> None:
    """Minimal QGIS categorized style on kgco2e_per_m2 (stretch)."""
    cats = "".join(f'<category symbol="{i}" value="{b:.4f}" label="up to {b:.4f}"/>' for i, b in enumerate(breaks[1:]))
    syms = "".join(
        f'<symbol name="{i}" type="fill"><layer class="SimpleFill">'
        f'<prop k="color" v="{_ramp(i, len(breaks) - 1)}"/>'
        "</layer></symbol>"
        for i in range(len(breaks) - 1)
    )
    qml = (
        '<?xml version="1.0"?><qgis version="3.34"><renderer-v2 type="categorized" '
        f'attr="kgco2e_per_m2">{cats}<symbols>{syms}</symbols></renderer-v2></qgis>'
    )
    ET.fromstring(qml)  # well-formedness check
    path.write_text(qml, encoding="utf-8")


def _ramp(i: int, n: int) -> str:
    pal = ["229,245,224", "199,233,192", "161,217,155", "116,196,118", "65,171,93", "35,139,69", "0,109,44"]
    return pal[min(i, len(pal) - 1)] if n <= 1 else pal[min(int(i / max(n - 1, 1) * 6), 6)]


def main() -> int:
    import geopandas as gpd
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT.mkdir(parents=True, exist_ok=True)
    raw = gpd.read_file(CACHE)
    print(f"raw footprints: {len(raw)}")
    clean = clean_footprints(raw)
    proj = footprint_area_m2(to_projected(clean))
    print(f"kept: {len(proj)}")

    gia, gas, inten = load_metrics()
    ids = sorted(gia, key=lambda b: gia[b], reverse=True)
    cand = proj.nlargest(max(len(ids) * 4, 12), "footprint_m2").copy()
    assigned = assign_ids_by_area(cand, [(b, gia[b]) for b in ids])
    matched = assigned[assigned.building_id.notna()].copy()
    matched["gia_m2"] = matched.building_id.map(gia)
    matched["gas_kwh"] = matched.building_id.map(gas).fillna(0.0)
    matched["kgco2e_per_m2"] = matched.building_id.map(inten)
    matched["storeys"] = [implied_storeys(g, f) for g, f in zip(matched.gia_m2, matched.footprint_m2)]
    matched["storey_flag"] = [flag_storey_outlier(s) for s in matched.storeys]
    print(f"matched buildings: {len(matched)}; flags: {matched.storey_flag.sum()}")

    matrix = centroid_distance_matrix(matched)
    labels = cluster_within(matrix, 300.0)
    matched["heat_cluster"] = labels
    gas_by_cluster = cluster_totals(labels, list(matched.gas_kwh))
    print("clusters:", len(set(labels)), "gas/cluster:", {k: round(v, 1) for k, v in gas_by_cluster.items()})

    web = matched.to_crs(WGS84)
    keep = [
        "building_id",
        "anon_name",
        "footprint_m2",
        "gia_m2",
        "gas_kwh",
        "kgco2e_per_m2",
        "storeys",
        "storey_flag",
        "heat_cluster",
        "geometry",
    ]
    web = web[keep]
    web.to_file(OUT / "campus_carbon.gpkg", layer="buildings", driver="GPKG")
    web.to_file(OUT / "campus_carbon.geojson", driver="GeoJSON")
    import topojson

    topojson.Topology(web, prequantize=True).to_json(str(OUT / "campus_carbon.topojson"))
    print("wrote gpkg/geojson/topojson")

    # Isochrones around the largest building (centroid in projected CRS, then to lon/lat).
    origin = matched.sort_values("footprint_m2", ascending=False).iloc[0]
    origin_pt = gpd.GeoSeries([origin.geometry], crs=PROJECTED_CRS).centroid.to_crs(WGS84).iloc[0]
    lon0, lat0 = float(origin_pt.x), float(origin_pt.y)
    bbox = tuple(json.loads(CACHE.with_suffix(".log.json").read_text())["bbox_wsen"])
    G = load_graph(bbox)
    iso = isochrones(G, lon0, lat0)
    iso_gdf = gpd.GeoDataFrame({"mins": list(iso.keys())}, geometry=list(iso.values()), crs=PROJECTED_CRS).to_crs(WGS84)
    iso_gdf.to_file(OUT / "isochrones.geojson", driver="GeoJSON")

    # Lat/long point extract for the Power BI bubble-map fallback.
    cents = matched.copy()
    cents["geometry"] = cents.geometry.centroid
    cents = cents.to_crs(WGS84)
    pts = web.merge(
        cents[["building_id", "geometry"]].rename(columns={"geometry": "pt"}),
        on="building_id",
        how="left",
    )
    pts["lon"] = pts.pt.x
    pts["lat"] = pts.pt.y
    pts[["building_id", "anon_name", "lat", "lon", "kgco2e_per_m2", "gas_kwh"]].to_csv(
        OUT / "building_points.csv", index=False
    )

    # Static PNGs.
    fig, ax = plt.subplots(figsize=(8, 8))
    matched.plot(column="kgco2e_per_m2", legend=True, ax=ax, cmap="YlGn")
    ax.set_title("kgCO2e/m2 by building (synthetic metrics on public geometry)")
    ax.set_axis_off()
    fig.savefig(OUT / "choropleth.png", dpi=150, bbox_inches="tight")
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    matched.plot(column="heat_cluster", categorical=True, legend=True, ax=ax2, cmap="tab10")
    iso_proj = iso_gdf.to_crs(PROJECTED_CRS)
    iso_proj[iso_proj.mins == "10min"].plot(ax=ax2, facecolor="none", edgecolor="red", linewidth=2, label="10 min")
    iso_proj[iso_proj.mins == "5min"].plot(ax=ax2, facecolor="red", edgecolor="darkred", alpha=0.15, label="5 min")
    ax2.set_title("Heat clusters (300 m) + 5/10-min isochrones — screening only")
    ax2.set_axis_off()
    fig2.savefig(OUT / "clusters_isochrones.png", dpi=150, bbox_inches="tight")
    plt.close("all")

    # Folium.
    import folium

    m = folium.Map(location=[lat0, lon0], zoom_start=16, tiles="CartoDB positron")
    breaks = quantile_breaks([float(v) for v in matched.kgco2e_per_m2 if v is not None])
    folium.Choropleth(
        geo_data=web.to_json(),
        data=web,
        columns=["building_id", "kgco2e_per_m2"],
        key_on="feature.properties.building_id",
        fill_color="YlGn",
        legend_name="kgCO2e/m2 (synthetic)",
    ).add_to(m)
    for _, r in web.iterrows():
        folium.Marker(
            [r.geometry.centroid.y, r.geometry.centroid.x],
            popup=f"{r.anon_name} ({r.building_id}): {r.kgco2e_per_m2:.4f} kgCO2e/m2",
        ).add_to(m)
    folium.GeoJson(iso_gdf.to_json(), name="isochrones").add_to(m)
    folium.LayerControl().add_to(m)
    m.get_root().html.add_child(
        folium.Element("<p><small>Synthetic metrics on public geometry (c) OpenStreetMap contributors</small></p>")
    )
    m.save(OUT / "campus_carbon.html")

    write_qml(OUT / "campus_carbon.qml", breaks)
    log = {
        "matched": int(len(matched)),
        "storey_flags": int(matched.storey_flag.sum()),
        "clusters": len(set(labels)),
        "gas_kwh_by_cluster": {str(k): round(v, 1) for k, v in gas_by_cluster.items()},
        "isochrone_origin": origin.building_id,
        "outputs": sorted(p.name for p in OUT.iterdir()),
    }
    (OUT / "build.log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
