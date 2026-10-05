"""Streamlit mirror of the P08 carbon dashboard (synthetic demo).

Run from the repo root:  streamlit run projects/p08-net-zero-carbon/streamlit_app.py
Reads gold marts from data/warehouse.duckdb (read-only).
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB = Path("data/warehouse.duckdb")
st.set_page_config(page_title="Net zero & carbon (synthetic demo)", layout="wide")
st.title("Net zero & carbon — synthetic portfolio demo")
st.caption("Synthetic data for portfolio demonstration.")


@st.cache_data
def q(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


scopes = q(
    """SELECT f.scope, SUM(d.kwh) AS kwh, SUM(d.kwh * f.factor_kgco2e_per_kwh) AS kgco2e
       FROM main.fct_energy_daily d
       JOIN main.dim_emission_factor f
         ON f.fuel = CASE d.utility WHEN 'electricity' THEN 'electricity'
                                     WHEN 'gas' THEN 'natural_gas' END
       GROUP BY 1 ORDER BY 1"""
)
c1, c2, c3 = st.columns(3)
c1.metric("Scope 1 kgCO2e", f"{scopes.loc[0, 'kgco2e']:,.0f}")
c2.metric("Scope 2 kgCO2e", f"{scopes.loc[1, 'kgco2e']:,.0f}")
c3.metric("Total kgCO2e", f"{scopes['kgco2e'].sum():,.0f}")

st.subheader("Monthly emissions by fuel")
monthly = q("SELECT month, fuel, kwh, kgco2e FROM main.mart_carbon_monthly ORDER BY month, fuel")
st.bar_chart(monthly, x="month", y="kgco2e", color="fuel")

st.subheader("Intensity league (kgCO2e/m²)")
league = q(
    """SELECT d.building_id, ROUND(SUM(d.kwh * f.factor_kgco2e_per_kwh) / MAX(b.gia_m2), 4) AS kgco2e_per_m2
       FROM main.fct_energy_daily d
       JOIN main.dim_building b USING (building_id)
       JOIN main.dim_emission_factor f
         ON f.fuel = CASE d.utility WHEN 'electricity' THEN 'electricity'
                                     WHEN 'gas' THEN 'natural_gas' END
       GROUP BY 1 ORDER BY 2 DESC"""
)
st.dataframe(league, use_container_width=True)

st.subheader("Method note")
st.markdown(
    "Location-based Scope 2 (DESNZ 2025 factors), Scope 1 gas. "
    "See `methodology.md` for boundaries, HDD normalisation limits and the "
    "market-based illustrative placeholder rule."
)
