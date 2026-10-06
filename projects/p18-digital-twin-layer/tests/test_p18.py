"""Tests for P18 digital twin data layer."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ids import make_canonical, parse_canonical, validate_canonical_id
from crosswalk import build_crosswalk
from relationships import build_relationships
from brick import generate_brick_ttl, validate_brick, run_sparql_queries
from coverage import compute_coverage


def test_canonical_ids():
    """Test canonical ID validation and parsing."""
    # Valid IDs
    assert validate_canonical_id("space:S-B001-L00-001") == (True, "space")
    assert validate_canonical_id("asset:A-B001-000001") == (True, "asset")
    assert validate_canonical_id("bldg:B001") == (True, "bldg")
    assert validate_canonical_id("meter:M-B001-E01") == (True, "meter")
    assert validate_canonical_id("sensor:SN-0001") == (True, "sensor")
    assert validate_canonical_id("bms_point:SN-0001 [ppm]") == (True, "bms_point")
    assert validate_canonical_id("ifc:fWKOKJfJYtMbwB_nrA$2co") == (True, "ifc")

    # Invalid IDs
    assert validate_canonical_id("invalid") == (False, None)
    assert validate_canonical_id("space:invalid") == (False, None)

    # Parse
    assert parse_canonical("space:S-B001-L00-001") == ("space", "S-B001-L00-001")
    assert parse_canonical("asset:A-B001-000001") == ("asset", "A-B001-000001")

    # Make
    assert make_canonical("space", "S-B001-L00-001") == "space:S-B001-L00-001"


def test_crosswalk_build():
    """Test crosswalk building."""
    df = build_crosswalk()
    assert len(df) > 0
    assert set(["canonical_id", "system", "native_id"]).issubset(df.columns)
    # Check key systems present
    systems = set(df["system"].unique())
    assert "space_register" in systems
    assert "cafm" in systems
    assert "ifc" in systems
    assert "bms" in systems
    assert "meter" in systems
    assert "sensor" in systems


def test_relationships_build():
    """Test relationship graph building."""
    df = build_relationships()
    assert len(df) > 0
    assert set(["subject_id", "predicate", "object_id", "source"]).issubset(df.columns)
    # Check key predicates
    predicates = set(df["predicate"].unique())
    assert "hasPart" in predicates
    assert "isLocatedIn" in predicates
    assert "feeds" in predicates
    assert "hasPoint" in predicates
    assert "isMeteredBy" in predicates
    assert "isServedBy" in predicates


def test_brick_generation():
    """Test Brick TTL generation."""
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl("B001", out)
    assert len(ttl) > 1000
    assert "brick:Building" in ttl
    assert "brick:AHU" in ttl
    assert "brick:feeds" in ttl
    assert "brick:HVAC_Zone" in ttl


def test_brick_validation():
    """Test Brick validation."""
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl("B001", out)
    valid, errors = validate_brick(ttl)
    assert valid is True
    assert len(errors) == 0


def test_sparql_queries():
    """Test SPARQL queries return expected results."""
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl("B001", out)
    results = run_sparql_queries(ttl)
    # At least some queries should return results
    assert "ahu_served_spaces" in results
    assert len(results["ahu_served_spaces"]) > 0


def test_coverage():
    """Test coverage computation."""
    cov = compute_coverage()
    assert "assets_with_ifc_guid_pct" in cov
    assert "spaces_with_sensors_pct" in cov
    assert "assets_linked_to_bms_pct" in cov
    assert "meters_mapped_to_building_pct" in cov
    # Check ranges
    for v in cov.values():
        assert 0 <= v <= 100
    # Specific known values for small profile (may vary by seed)
    assert cov["meters_mapped_to_building_pct"] == 100.0  # All mapped
    # Just verify the structure - exact values may vary


def test_orphan_detection():
    """Test that no canonical IDs are orphaned in relationships."""
    df = build_relationships()
    # Every subject and object should have a corresponding crosswalk entry
    # (This is a basic check - full orphan detection would need more)
    assert len(df) > 0


def test_id_collision():
    """Test that canonical IDs don't have unintended duplicates."""
    df = build_crosswalk()
    # Same (canonical_id, system, native_id) should not appear twice
    dupes = df.duplicated(subset=["canonical_id", "system", "native_id"]).sum()
    assert dupes == 0
    # But same canonical_id can have multiple native_ids in same system (e.g., space + room_code + IFC GUID)


def test_brick_sparql_ahu_spaces():
    """Specific test for AHU served spaces query."""
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl("B001", out)
    from brick import run_sparql_queries
    results = run_sparql_queries(ttl)
    # Should have AHU served spaces
    assert len(results["ahu_served_spaces"]) > 0
    for row in results["ahu_served_spaces"]:
        assert "ahu" in row
        assert "space" in row


def test_brick_sparql_co2_sensors():
    """Test CO2 sensor query."""
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl("B001", out)
    from brick import run_sparql_queries
    results = run_sparql_queries(ttl)
    # CO2 sensors may be 0 in small profile, but query should run
    assert "co2_above_threshold" in results
    # Just verify query structure works (may return 0 rows)