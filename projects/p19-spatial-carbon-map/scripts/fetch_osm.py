"""OSM footprint fetch (P19) — public geometry only, cached, reproducible.

Usage (repo root):
  python projects/p19-spatial-carbon-map/scripts/fetch_osm.py [--dist M] [--out FILE]

Default: University of Exeter Streatham campus area (arbitrary campus default
per spec; any university bbox works). Writes a retrieval log beside the cache.
Licence: OpenStreetMap contributors, ODbL (see DATA.md).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

DEFAULT_LAT = 50.736
DEFAULT_LON = -3.534


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch OSM building footprints.")
    p.add_argument("--lat", type=float, default=DEFAULT_LAT)
    p.add_argument("--lon", type=float, default=DEFAULT_LON)
    p.add_argument("--dist", type=float, default=800.0, help="Half side, metres.")
    p.add_argument("--out", default="data/reference/osm_buildings.geojson")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    import osmnx as ox

    args = parse_args(argv)
    out = Path(args.out)
    if out.exists():
        print(f"cache hit: {out} (delete to re-fetch)")
        return 0
    bbox = ox.utils_geo.bbox_from_point((args.lat, args.lon), dist=args.dist)
    print(f"fetching buildings in bbox {tuple(round(float(v), 5) for v in bbox)} ...")
    gdf = ox.features_from_bbox(bbox, tags={"building": True})
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out, driver="GeoJSON")
    log = {
        "source": "OpenStreetMap via osmnx/Overpass",
        "licence": "ODbL (c) OpenStreetMap contributors",
        "bbox_wsen": [float(v) for v in bbox],
        "center_lat_lon": [args.lat, args.lon],
        "dist_m": args.dist,
        "retrieved_utc": dt.datetime.now(dt.UTC).isoformat(),
        "features": int(len(gdf)),
        "out": str(out),
    }
    out.with_suffix(".log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(gdf)} features)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
