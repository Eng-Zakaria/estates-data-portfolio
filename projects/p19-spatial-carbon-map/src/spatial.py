"""Spatial primitives (P19) — pure functions, offline-testable.

Conventions: analysis in a projected CRS (default EPSG:27700 for the UK
default bbox); web exports in EPSG:4326. All metrics synthetic; only the
footprint geometry is public (OSM, ODbL).
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

PROJECTED_CRS = "EPSG:27700"
WGS84 = "EPSG:4326"

# OSM building values treated as non-estate (houses, sheds...) and dropped.
DOMESTIC_VALUES = {
    "house",
    "residential",
    "apartments",
    "detached",
    "semidetached_house",
    "terrace",
    "garage",
    "garages",
    "shed",
    "sheds",
    "barn",
    "farm",
    "greenhouse",
    "boathouse",
    "cabin",
    "hut",
    "static_caravan",
}


def clean_footprints(gdf: gpd.GeoDataFrame, building_col: str = "building") -> gpd.GeoDataFrame:
    """Keep valid, non-empty (Multi)Polygons; drop domestic building values."""
    out = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    if building_col in out.columns:
        out = out[~out[building_col].isin(DOMESTIC_VALUES)]
    out["geometry"] = out.geometry.make_valid()
    out = out[~out.geometry.is_empty]
    return out.reset_index(drop=True)


def to_projected(gdf: gpd.GeoDataFrame, epsg: str = PROJECTED_CRS) -> gpd.GeoDataFrame:
    """Project to a metric CRS for area/distance work."""
    return gdf.to_crs(epsg)


def footprint_area_m2(gdf_projected: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add footprint_m2 (requires a projected, metric CRS)."""
    out = gdf_projected.copy()
    out["footprint_m2"] = out.geometry.area
    return out


def implied_storeys(gia_m2: float, footprint_m2: float | None) -> float | None:
    """GIA / footprint as a sanity ratio. None when footprint missing/zero."""
    if footprint_m2 is None or footprint_m2 <= 0:
        return None
    return gia_m2 / footprint_m2


def flag_storey_outlier(storeys: float | None, lo: float = 1.0, hi: float = 12.0) -> bool | None:
    """Flag implausible implied storeys (footprint != floor area signal)."""
    if storeys is None:
        return None
    return bool(storeys < lo or storeys > hi)


def assign_ids_by_area(
    footprints: gpd.GeoDataFrame,
    buildings: list[tuple[str, float]],
) -> gpd.GeoDataFrame:
    """Assign synth building IDs by area-rank match (largest footprint ↔ largest GIA).

    Deterministic. Adds building_id + anon_name ("Building A"...). Extra
    footprints beyond the building list are left unassigned (None).
    """
    order = footprints.sort_values("footprint_m2", ascending=False).reset_index(drop=True)
    ranked = sorted(buildings, key=lambda b: b[1], reverse=True)
    ids: list[str | None] = [ranked[i][0] if i < len(ranked) else None for i in range(len(order))]
    names = [f"Building {chr(65 + i)}" for i in range(len(order))]
    order["building_id"] = ids
    order["anon_name"] = names
    return order


def centroid_distance_matrix(points: gpd.GeoDataFrame) -> list[list[float]]:
    """Pairwise centroid distances in CRS units (metres when projected)."""
    cents = list(points.geometry.centroid)
    return [[float(a.distance(b)) for b in cents] for a in cents]


def cluster_within(matrix: list[list[float]], threshold_m: float) -> list[int]:
    """Greedy single-linkage clustering: labels in first-seen order."""
    n = len(matrix)
    label = [-1] * n
    current = 0
    for i in range(n):
        if label[i] != -1:
            continue
        label[i] = current
        stack = [i]
        while stack:
            a = stack.pop()
            for b in range(n):
                if label[b] == -1 and matrix[a][b] <= threshold_m:
                    label[b] = current
                    stack.append(b)
        current += 1
    return label


def cluster_totals(labels: list[int], values: list[float]) -> dict[int, float]:
    """Sum values per cluster label."""
    totals: dict[int, float] = {}
    for lab, val in zip(labels, values):
        totals[lab] = totals.get(lab, 0.0) + val
    return totals


def quantile_breaks(values: list[float], k: int = 5) -> list[float]:
    """Monotonic choropleth class breaks (quantiles)."""
    import statistics

    if not values:
        return []
    qs = statistics.quantiles(sorted(values), n=k + 1, method="inclusive")
    return [float(v) for v in [min(values), *qs[1:-1], max(values)]]


def hull_of_points(points: gpd.GeoDataFrame) -> Polygon | MultiPolygon | None:
    """Convex hull screening polygon for a reachable-node set (or None)."""
    if len(points) == 0:
        return None
    return points.geometry.union_all().convex_hull
