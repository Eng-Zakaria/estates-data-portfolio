"""Streamlit mirror of the P06 space utilisation dashboard (synthetic demo).

Run from the repo root:  streamlit run projects/p06-space-utilisation/streamlit_app.py
Reads gold marts from data/warehouse.duckdb (read-only).
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB = Path("data/warehouse.duckdb")
st.set_page_config(page_title="Space utilisation (synthetic demo)", layout="wide")
st.title("Space utilisation — synthetic portfolio demo")
st.caption("Synthetic data for portfolio demonstration.")


@st.cache_data
def q(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


kpi = q(
    """SELECT COUNT(*) n_spaces, SUM(booked_hours) booked,
              AVG(frequency_rate) freq, AVG(occupancy_rate) occ,
              AVG(frequency_rate * occupancy_rate) util
       FROM main.mart_space_utilisation"""
).iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Spaces", f"{kpi['n_spaces']:.0f}")
c2.metric("Frequency %", f"{100 * kpi['freq']:.1f}%")
c3.metric("Occupancy %", f"{100 * kpi['occ']:.1f}%")
c4.metric("Utilisation %", f"{100 * kpi['util']:.1f}%")

st.subheader("Rooms to review (lowest utilisation)")
rooms = q(
    """SELECT space_id, building_id, space_category, n_events,
              ROUND(booked_hours, 1) booked_hours,
              ROUND(frequency_rate, 3) freq, ROUND(occupancy_rate, 3) occ,
              ROUND(frequency_rate * occupancy_rate, 3) util
       FROM main.mart_space_utilisation
       ORDER BY util ASC NULLS LAST LIMIT 20"""
)
st.dataframe(rooms, use_container_width=True)

st.subheader("Utilisation by building")
bld = q(
    """SELECT building_id, ROUND(AVG(frequency_rate * occupancy_rate), 4) util
       FROM main.mart_space_utilisation GROUP BY 1 ORDER BY 2 DESC"""
)
st.bar_chart(bld, x="building_id", y="util")

st.subheader("Method note")
st.markdown(
    "Frequency = booked / available (teaching days x 9h); "
    "occupancy = avg group / capacity; utilisation = frequency x occupancy. "
    "See `methodology.md`. No-show detail needs sensor coverage — see "
    "`validation/v02_rooms_to_review.sql`."
)
