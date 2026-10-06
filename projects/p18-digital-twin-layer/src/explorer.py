"""Streamlit explorer UI for the digital twin (P18).

Run: streamlit run projects/p18-digital-twin-layer/src/explorer.py
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Digital Twin Explorer (synthetic)", layout="wide")
st.title("Campus Digital Twin Explorer — synthetic demo")
st.caption("Synthetic data for portfolio demonstration.")


@st.cache_data
def load_buildings():
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        return con.execute("SELECT * FROM main.dim_building").df()
    finally:
        con.close()


@st.cache_data
def load_spaces(building_id: str):
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        return con.execute(
            "SELECT * FROM main.dim_space WHERE building_id = ?", [building_id]
        ).df()
    finally:
        con.close()


@st.cache_data
def load_assets(building_id: str = None, space_id: str = None):
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        if space_id:
            return con.execute(
                "SELECT * FROM main.dim_asset WHERE space_id = ?", [space_id]
            ).df()
        elif building_id:
            return con.execute(
                "SELECT a.* FROM main.dim_asset a JOIN main.dim_space s ON s.space_id = a.space_id WHERE s.building_id = ?",
                [building_id],
            ).df()
        else:
            return con.execute("SELECT * FROM main.dim_asset").df()
    finally:
        con.close()


@st.cache_data
def load_sensors(space_id: str):
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        return con.execute(
            "SELECT * FROM main.stg_truth__sensor WHERE space_id = ?", [space_id]
        ).df()
    finally:
        con.close()


@st.cache_data
def load_relationships():
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        return con.execute(
            "SELECT * FROM read_parquet('projects/p18-digital-twin-layer/outputs/relationship.parquet')"
        ).df()
    except Exception:
        return pd.DataFrame()
    finally:
        con.close()


# Sidebar: building selector
buildings = load_buildings()
bldg_choice = st.sidebar.selectbox(
    "Building",
    buildings["building_id"].tolist(),
    format_func=lambda x: f"{x} ({buildings[buildings.building_id==x].building_name.values[0]})",
)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Building → Space → Asset", "Relationship Graph", "Sensor Trends", "Coverage"])

with tab1:
    st.subheader(f"Building {bldg_choice}")
    spaces = load_spaces(bldg_choice)
    st.metric("Spaces", len(spaces))

    # Space selector
    space_ids = spaces["space_id"].tolist()
    if space_ids:
        space_choice = st.selectbox("Space", space_ids, format_func=lambda x: f"{x} ({spaces[spaces.space_id==x].space_category.values[0]})")

        st.write("**Space Details**")
        space_info = spaces[spaces.space_id == space_choice].iloc[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Category", space_info["space_category"])
        col2.metric("NIA (m²)", f"{space_info['nia_m2']:.1f}")
        col3.metric("Capacity", int(space_info["capacity_seats"]))

        # Assets in space
        st.write("**Assets in this Space**")
        assets = load_assets(space_id=space_choice)
        if len(assets):
            st.dataframe(assets[["asset_id", "asset_type", "condition_grade", "criticality", "replacement_cost_gbp"]], use_container_width=True)

            # Asset selector
            if len(assets):
                asset_choice = st.selectbox("Asset for sensor trend", assets["asset_id"].tolist())
                # Sensor trend for assets in this space
                sensors = pd.DataFrame()
                try:
                    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
                    sensors = con.execute("""
                        SELECT s.sensor_id, s.sensor_type
                        FROM main.stg_truth__sensor s
                        JOIN main.dim_asset a ON a.space_id = s.space_id
                        WHERE a.asset_id IN (SELECT asset_id FROM main.dim_asset WHERE asset_id IN ({}))
                    """.format(",".join("?" * len(assets["asset_id"]))), assets["asset_id"].tolist()).df()
                except Exception:
                    pass

                if len(sensors):
                    sensor_choice = st.selectbox("Sensor", sensors["sensor_id"].tolist())
                    # Load recent readings
                    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
                    readings = con.execute("""
                        SELECT ts_utc, observed_count
                        FROM main.fct_space_observed_occupancy
                        WHERE sensor_id = ?
                        ORDER BY ts_utc DESC LIMIT 200
                    """, [sensors[sensors.sensor_id == sensor_choice].iloc[0]["sensor_id"]]).df()
                    con.close()

                    if len(readings):
                        st.line_chart(readings.set_index("ts_utc")["observed_count"])
        else:
            st.info("No assets in this space")

with tab2:
    st.subheader("Relationship Graph")
    rels = load_relationships()
    if len(rels):
        st.metric("Total Relationships", len(rels))
        st.write("**Predicates**")
        pred_counts = rels["predicate"].value_counts()
        st.bar_chart(pred_counts)

        # Filter by predicate
        pred_filter = st.multiselect("Filter predicates", rels["predicate"].unique().tolist())
        if pred_filter:
            filtered = rels[rels["predicate"].isin(pred_filter)]
        else:
            filtered = rels

        st.dataframe(filtered.head(1000), use_container_width=True)

        # Simple graph traversal demo
        st.write("**Traversal Demo: AHU → Spaces Served**")
        try:
            con = duckdb.connect("data/warehouse.duckdb", read_only=True)
            ahu_assets = con.execute("""
                SELECT asset_id FROM main.dim_asset
                WHERE asset_type IN ('AHU', 'AHU Controller', 'BMS Controller', 'Chiller')
                LIMIT 5
            """).df()
            con.close()

            if len(ahu_assets):
                ahu_choice = st.selectbox("Select AHU", ahu_assets["asset_id"].tolist())
                # Find spaces served by this AHU
                con = duckdb.connect("data/warehouse.duckdb", read_only=True)
                served = con.execute("""
                    SELECT DISTINCT s.space_id, s.room_code, s.space_category
                    FROM main.dim_space s
                    JOIN main.dim_asset a ON a.space_id = s.space_id
                    WHERE a.asset_id = ?
                """, [ahu_choice]).df()
                con.close()
                if len(served):
                    st.dataframe(served, use_container_width=True)
                else:
                    st.info("No spaces served by this AHU in the relationship graph")
        except Exception as e:
            st.error(f"Error: {e}")

with tab3:
    st.subheader("Sensor Trends")
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    sensors = con.execute("""
        SELECT s.sensor_id, s.sensor_type, s.space_id, sp.room_code
        FROM main.stg_truth__sensor s
        JOIN main.dim_space sp ON sp.space_id = s.space_id
    """).df()
    con.close()

    if len(sensors):
        sensor_choice = st.selectbox(
            "Sensor",
            sensors["sensor_id"].tolist(),
            format_func=lambda x: f"{x} ({sensors[sensors.sensor_id==x].sensor_type.values[0]}, {sensors[sensors.sensor_id==x].room_code.values[0]})",
        )

        con = duckdb.connect("data/warehouse.duckdb", read_only=True)
        readings = con.execute("""
            SELECT ts_utc, observed_count
            FROM main.fct_space_observed_occupancy
            WHERE sensor_id = ?
            ORDER BY ts_utc DESC LIMIT 500
        """, [sensor_choice]).df()
        con.close()

        if len(readings):
            readings["ts_utc"] = pd.to_datetime(readings["ts_utc"])
            st.line_chart(readings.set_index("ts_utc")["observed_count"])
            st.metric("Latest Reading", f"{readings.iloc[0]['observed_count']:.1f}")
            st.metric("Readings in Window", len(readings))

with tab4:
    st.subheader("Twin Coverage Report")
    from coverage import compute_coverage
    cov = compute_coverage()

    col1, col2 = st.columns(2)
    col1.metric("Assets with IFC GUID", f"{cov['assets_with_ifc_guid_pct']:.1f}%")
    col2.metric("Spaces with Sensors", f"{cov['spaces_with_sensors_pct']:.1f}%")

    col3, col4 = st.columns(2)
    col3.metric("Assets Linked to BMS", f"{cov['assets_linked_to_bms_pct']:.1f}%")
    col4.metric("Meters Mapped to Building", f"{cov['meters_mapped_to_building_pct']:.1f}%")

    st.write("**Notes**")
    st.write("- Assets with IFC GUID: 0% (truth parquet has NULL for all assets)")
    st.write("- Spaces with Sensors: ~6% (30 occupancy sensors across 495 spaces)")
    st.write("- Assets Linked to BMS: synthetic mapping via shared space")
    st.write("- Meters Mapped to Building: 100% (all 16 meters have building_id)")