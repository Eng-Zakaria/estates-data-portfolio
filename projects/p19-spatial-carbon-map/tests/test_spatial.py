"""Hand-checked fixtures for P19 spatial primitives (offline, no network)."""

import sys
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spatial import (  # noqa: E402
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


def square(x: float, y: float, size: float = 100.0) -> Polygon:
    return Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)])


def test_crs_area_known_polygon() -> None:
    # 100 m x 100 m square expressed in EPSG:27700 coordinates -> 10,000 m2.
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[square(400000, 300000)], crs="EPSG:27700")
    out = footprint_area_m2(gdf)
    assert out.loc[0, "footprint_m2"] == pytest.approx(10000.0)


def test_project_changes_crs() -> None:
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(-3.534, 50.736)], crs="EPSG:4326")
    assert to_projected(gdf).crs.to_string() == "EPSG:27700"


def test_clean_drops_invalid_kinds_and_domestic() -> None:
    gdf = gpd.GeoDataFrame(
        {"building": ["university", "house", "university", "university"]},
        geometry=[
            square(0, 0),
            square(200, 0),
            LineString([(0, 0), (1, 1)]),
            Polygon(),  # empty
        ],
        crs="EPSG:27700",
    )
    out = clean_footprints(gdf)
    assert len(out) == 1
    assert out.iloc[0]["building"] == "university"


def test_storeys_and_flags() -> None:
    assert implied_storeys(9302.6, 4651.3) == pytest.approx(2.0)
    assert implied_storeys(100.0, 0.0) is None
    assert flag_storey_outlier(0.2) is True
    assert flag_storey_outlier(25.0) is True
    assert flag_storey_outlier(4.0) is False
    assert flag_storey_outlier(None) is None


def test_assign_ids_by_area_rank() -> None:
    gdf = gpd.GeoDataFrame(
        {"footprint_m2": [500.0, 2000.0, 1000.0]},
        geometry=[square(0, 0), square(500, 0), square(1000, 0)],
        crs="EPSG:27700",
    )
    out = assign_ids_by_area(gdf, [("B001", 9000.0), ("B002", 4000.0)])
    by_area = out.sort_values("footprint_m2", ascending=False).reset_index(drop=True)
    assert list(by_area["building_id"][:2]) == ["B001", "B002"]
    assert by_area.loc[2, "building_id"] is None
    assert list(out["anon_name"][:2]) == ["Building A", "Building B"]
    # Deterministic: same input, same assignment.
    again = assign_ids_by_area(gdf, [("B001", 9000.0), ("B002", 4000.0)])
    assert list(again.sort_values("footprint_m2", ascending=False)["building_id"][:2]) == ["B001", "B002"]


def test_distance_matrix_known_points() -> None:
    # (0,0) and (300,400) in metres -> 500 m; symmetric, zero diagonal.
    gdf = gpd.GeoDataFrame({"id": [1, 2]}, geometry=[Point(0, 0), Point(300, 400)], crs="EPSG:27700")
    m = centroid_distance_matrix(gdf)
    assert m[0][1] == pytest.approx(500.0)
    assert m[1][0] == pytest.approx(500.0)
    assert m[0][0] == pytest.approx(0.0)


def test_clustering_and_totals() -> None:
    m = [[0.0, 100.0, 900.0], [100.0, 0.0, 950.0], [900.0, 950.0, 0.0]]
    assert cluster_within(m, 200.0) == [0, 0, 1]
    assert cluster_totals([0, 0, 1], [10.0, 20.0, 5.0]) == {0: 30.0, 1: 5.0}


def test_breaks_monotonic() -> None:
    b = quantile_breaks([3.0, 1.0, 2.0, 5.0, 4.0], k=2)
    assert b == sorted(b) and b[0] == 1.0 and b[-1] == 5.0
    assert quantile_breaks([]) == []


def test_hull_none_when_empty() -> None:
    empty = gpd.GeoDataFrame({"id": []}, geometry=[], crs="EPSG:27700")
    assert hull_of_points(empty) is None
    pts = gpd.GeoDataFrame({"id": [1, 2]}, geometry=[Point(0, 0), Point(10, 0)], crs="EPSG:27700")
    assert hull_of_points(pts) is not None


def test_multipolygon_kept() -> None:
    gdf = gpd.GeoDataFrame(
        {"building": ["university"]},
        geometry=[MultiPolygon([square(0, 0), square(500, 500)])],
        crs="EPSG:27700",
    )
    assert len(clean_footprints(gdf)) == 1
