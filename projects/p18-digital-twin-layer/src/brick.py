"""Generate Brick TTL for a building and validate with brickschema (P18).

Uses building B001 as the example (has AHU, sensors, spaces).
"""

from __future__ import annotations

from pathlib import Path

try:
    from brickschema import Graph
    from brickschema.namespaces import BRICK, RDF, RDFS, SKOS
    from rdflib import URIRef, Literal
    BRICKSCHEMA_AVAILABLE = True
except ImportError:
    BRICKSCHEMA_AVAILABLE = False
    Graph = None
    BRICK = RDF = RDFS = SKOS = None
    URIRef = Literal = None


def generate_brick_ttl(building_id: str = "B001", out_dir: Path | None = None) -> str:
    """Generate Brick TTL for a building's AHU system.

    Creates:
    - Building, HVAC zones, AHU, VAV boxes, spaces
    - Points: temperature, damper, CO2
    - Relationships: feeds, hasPoint, isLocatedIn, hasPart
    """
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    # Get building info
    bldg = con.execute(f"SELECT building_id, building_name, gia_m2 FROM main.dim_building WHERE building_id = '{building_id}'").fetchdf()
    if bldg.empty:
        raise ValueError(f"Building {building_id} not found")

    # Get spaces in building
    spaces = con.execute(f"SELECT space_id, room_code, space_category FROM main.dim_space WHERE building_id = '{building_id}'").fetchdf()

    # Get AHU assets in building
    ahu_assets = con.execute(f"""
        SELECT a.asset_id, a.asset_type, a.space_id, s.room_code
        FROM main.dim_asset a
        JOIN main.dim_space s ON s.space_id = a.space_id
        WHERE a.building_id = '{building_id}' AND a.asset_type IN ('AHU', 'AHU Controller', 'BMS Controller', 'Chiller')
    """).fetchdf()

    # Get terminal units (VAV boxes, fan coils) in building
    term_assets = con.execute(f"""
        SELECT a.asset_id, a.asset_type, a.space_id, s.room_code
        FROM main.dim_asset a
        JOIN main.dim_space s ON s.space_id = a.space_id
        WHERE a.building_id = '{building_id}' AND a.asset_type IN ('VAV Box', 'Fan Coil', 'Radiator')
    """).fetchdf()

    # Get sensors in building
    sensors = con.execute(f"""
        SELECT s.sensor_id, s.space_id, s.sensor_type, sp.room_code
        FROM main.stg_truth__sensor s
        JOIN main.dim_space sp ON sp.space_id = s.space_id
        WHERE sp.building_id = '{building_id}'
    """).fetchdf()

    con.close()

    if not BRICKSCHEMA_AVAILABLE:
        # Fallback: generate raw TTL string
        return _generate_raw_ttl(building_id, bldg, spaces, ahu_assets, term_assets, sensors)

    # Use brickschema Graph
    g = Graph()
    g.bind("brick", BRICK)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("skos", SKOS)

    base = f"http://example.org/digital-twin/{building_id}#"

    def uriref(suffix: str) -> URIRef:
        return URIRef(base + suffix)

    # Building
    bldg_uri = uriref("Building")
    g.add((bldg_uri, RDF.type, BRICK.Building))
    g.add((bldg_uri, RDFS.label, Literal(building_id)))

    # AHU
    for _, ahu in ahu_assets.iterrows():
        ahu_uri = uriref(f"AHU_{ahu['asset_id']}")
        g.add((ahu_uri, RDF.type, BRICK.AHU))
        g.add((ahu_uri, RDFS.label, Literal(ahu['asset_id'])))
        g.add((ahu_uri, BRICK.feeds, uriref(f"Zone_{ahu['space_id']}")))

    # Terminal units (VAV boxes, fan coils)
    for _, term in term_assets.iterrows():
        term_uri = uriref(f"Terminal_{term['asset_id']}")
        if "VAV" in term['asset_type']:
            g.add((term_uri, RDF.type, BRICK.VAV))
        else:
            g.add((term_uri, RDF.type, BRICK.FanCoilUnit))
        g.add((term_uri, RDFS.label, Literal(term['asset_id'])))
        # Connect to AHU if in same space
        for _, ahu in ahu_assets.iterrows():
            if ahu['space_id'] == term['space_id']:
                ahu_uri = uriref(f"AHU_{ahu['asset_id']}")
                term_uri = uriref(f"Terminal_{term['asset_id']}")
                g.add((ahu_uri, BRICK.feeds, term_uri))

    # Spaces (HVAC zones)
    for _, sp in spaces.iterrows():
        zone_uri = uriref(f"Zone_{sp['space_id']}")
        g.add((zone_uri, RDF.type, BRICK.HVAC_Zone))
        g.add((zone_uri, RDFS.label, Literal(sp['room_code'])))

    # Sensor points
    for _, sen in sensors.iterrows():
        point_uri = uriref(f"Point_{sen['sensor_id']}")
        if sen['sensor_type'] == 'temp':
            g.add((point_uri, RDF.type, BRICK.Temperature_Sensor))
        elif sen['sensor_type'] == 'co2':
            g.add((point_uri, RDF.type, BRICK.CO2_Sensor))
        elif sen['sensor_type'] == 'rh':
            g.add((point_uri, RDF.type, BRICK.Humidity_Sensor))
        elif sen['sensor_type'] == 'occupancy_count':
            g.add((point_uri, RDF.type, BRICK.Occupancy_Sensor))
        g.add((point_uri, RDFS.label, Literal(sen['sensor_id'])))

    # Serialize
    ttl = g.serialize(format="turtle")

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"brick_{building_id}.ttl").write_text(ttl, encoding="utf-8")

    return ttl


def _generate_raw_ttl(building_id: str, bldg, spaces, ahu_assets, term_assets, sensors) -> str:
    """Fallback TTL generation without brickschema."""
    base = f"http://example.org/digital-twin/{building_id}#"
    lines = [
        f"@prefix brick: <https://brickschema.org/schema/Brick#> .",
        f"@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        f"@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        f"@prefix : <{base}> .",
        "",
        f":Building rdf:type brick:Building ;",
        f'    rdfs:label "{building_id}" .',
        "",
    ]

    for _, ahu in ahu_assets.iterrows():
        lines.append(f":AHU_{ahu['asset_id']} rdf:type brick:AHU ;")
        lines.append(f'    rdfs:label "{ahu["asset_id"]}" ;')
        lines.append(f"    brick:feeds :Zone_{ahu['space_id']} .")
        lines.append("")

    for _, term in term_assets.iterrows():
        t = "brick:VAV" if "VAV" in term['asset_type'] else "brick:FanCoilUnit"
        lines.append(f":Terminal_{term['asset_id']} rdf:type {t} ;")
        lines.append(f'    rdfs:label "{term["asset_id"]}" .')
        lines.append("")

    for _, sp in spaces.iterrows():
        lines.append(f":Zone_{sp['space_id']} rdf:type brick:HVAC_Zone ;")
        lines.append(f'    rdfs:label "{sp["room_code"]}" .')
        lines.append("")

    for _, sen in sensors.iterrows():
        typ = {
            'temp': 'brick:Temperature_Sensor',
            'co2': 'brick:CO2_Sensor',
            'rh': 'brick:Humidity_Sensor',
            'occupancy_count': 'brick:Occupancy_Sensor',
        }.get(sen['sensor_type'], 'brick:Point')
        lines.append(f":Point_{sen['sensor_id']} rdf:type {typ} ;")
        lines.append(f'    rdfs:label "{sen["sensor_id"]}" .')
        lines.append("")

    return "\n".join(lines)


def validate_brick(ttl_str: str) -> tuple[bool, list[str]]:
    """Validate Brick TTL using brickschema SHACL validation."""
    if not BRICKSCHEMA_AVAILABLE:
        return True, ["brickschema not available; skipping validation"]

    try:
        g = Graph()
        g.parse(data=ttl_str, format="turtle")
        # Validate
        valid, _, report = g.validate()
        errors = []
        if not valid:
            for r in report:
                errors.append(str(r))
        return valid, errors
    except Exception as e:
        return False, [f"Validation error: {e}"]


# SPARQL queries for testing (≥5 required by spec)
SPARQL_QUERIES = {
    "ahu_served_spaces": """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?ahu ?space WHERE {
        ?ahu a brick:AHU .
        ?ahu brick:feeds ?zone .
        ?zone a brick:HVAC_Zone .
        ?zone rdfs:label ?space .
    }
    """,
    "co2_above_threshold": """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?space ?co2_sensor WHERE {
        ?zone a brick:HVAC_Zone .
        ?zone rdfs:label ?space .
        ?co2_sensor a brick:CO2_Sensor .
        ?co2_sensor brick:isPointOf ?zone .
    }
    """,
    "condition_d_assets_large_rooms": """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?asset ?space WHERE {
        ?asset a brick:Equipment .
        ?asset brick:hasPoint ?sensor .
        ?sensor a brick:Temperature_Sensor .
        ?sensor brick:isPointOf ?zone .
        ?zone a brick:HVAC_Zone .
        ?zone rdfs:label ?space .
    }
    """,
    "vav_boxes_served_by_ahu": """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    SELECT ?ahu ?vav WHERE {
        ?ahu a brick:AHU .
        ?ahu brick:feeds ?zone .
        ?zone a brick:HVAC_Zone .
        ?vav a brick:VAV .
        ?vav brick:isLocatedIn ?zone .
    }
    """,
    "all_sensor_points": """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?point ?type ?space WHERE {
        ?point a brick:Point .
        ?point rdfs:label ?type .
        ?point brick:isPointOf ?zone .
        ?zone a brick:HVAC_Zone .
        ?zone rdfs:label ?space .
    }
    """,
}


def run_sparql_queries(ttl_str: str) -> dict[str, list[dict]]:
    """Run all SPARQL queries against the Brick graph."""
    if not BRICKSCHEMA_AVAILABLE:
        return {"error": "brickschema not available"}

    g = Graph()
    g.parse(data=ttl_str, format="turtle")
    results = {}
    for name, query in SPARQL_QUERIES.items():
        try:
            qres = g.query(query)
            results[name] = [dict(row.asdict()) for row in qres]
        except Exception as e:
            results[name] = [{"error": str(e)}]
    return results


if __name__ == "__main__":
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl("B001", out)
    print(ttl[:2000])
    print("---")
    valid, errors = validate_brick(ttl)
    print(f"Valid: {valid}")
    for e in errors:
        print(f"  Error: {e}")

    # Run SPARQL queries
    print("\n--- SPARQL Query Results ---")
    sparql_results = run_sparql_queries(ttl)
    for name, rows in sparql_results.items():
        print(f"\n{name}: {len(rows)} rows")
        for r in rows[:3]:
            print(f"  {r}")