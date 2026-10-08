"""Streamlit mirror of the P07 asset & maintenance dashboard (synthetic demo).

Run from the repo root:  streamlit run projects/p07-asset-maintenance/streamlit_app.py
Reads gold marts from data/warehouse.duckdb (read-only).
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB = Path("data/warehouse.duckdb")
st.set_page_config(page_title="Asset & maintenance (synthetic demo)", layout="wide")
st.title("Asset & maintenance — synthetic portfolio demo")
st.caption("Synthetic data for portfolio demonstration.")


@st.cache_data
def q(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


overview = q(
    """SELECT
         ROUND(SUM(CASE WHEN wo_type='PPM' AND status='Complete' THEN 1 ELSE 0 END)*1.0
               / NULLIF(SUM(CASE WHEN wo_type='PPM' THEN 1 ELSE 0 END),0), 4) AS ppm_completion,
         ROUND(SUM(CASE WHEN plan_category IN ('planned','other_planned') THEN 1 ELSE 0 END)*1.0
               / NULLIF(SUM(CASE WHEN wo_type='Reactive' THEN 1 ELSE 0 END),0), 2) AS planned_reactive,
         ROUND(AVG(days_to_complete) FILTER (WHERE wo_type='Reactive' AND status='Complete'), 2) AS mttr,
         ROUND(SUM(cost_gbp), 0) AS total_cost,
         COUNT(*) FILTER (WHERE is_open) AS backlog
       FROM main.fct_work_order"""
)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("PPM completion", f"{overview.loc[0, 'ppm_completion']:.1%}")
c2.metric("Planned : reactive", f"{overview.loc[0, 'planned_reactive']:.2f}")
c3.metric("MTTR (days)", f"{overview.loc[0, 'mttr']:.2f}")
c4.metric("Total cost £", f"£{overview.loc[0, 'total_cost']:,.0f}")
c5.metric("Backlog", f"{overview.loc[0, 'backlog']:.0f}")

st.subheader("Cost by trade")
trade = q("SELECT trade, ROUND(SUM(cost_gbp),0) AS cost FROM main.fct_work_order GROUP BY 1 ORDER BY 2 DESC")
st.bar_chart(trade, x="trade", y="cost")

st.subheader("Bad actors (top 10 by reactive jobs)")
bad = q(
    """SELECT h.asset_id, h.building_id, h.asset_type, h.reactive_12m,
              h.condition_grade, h.risk_score
       FROM main.mart_asset_health h
       ORDER BY h.reactive_12m DESC, h.risk_score DESC LIMIT 10"""
)
st.dataframe(bad, use_container_width=True)

st.subheader("PPM completion by month")
ppm = q(
    """SELECT STRFTIME(CAST(raised_ts AS TIMESTAMP), '%Y-%m') AS month,
              ROUND(COUNT(*) FILTER (WHERE status='Complete')*1.0/COUNT(*), 4) AS completion
       FROM main.fct_work_order WHERE wo_type='PPM' GROUP BY 1 ORDER BY 1"""
)
st.line_chart(ppm, x="month", y="completion")

st.subheader("5-year renewal forecast (£)")
renew = q(
    """SELECT year(install_date) + expected_life_years AS renewal_year,
              ROUND(SUM(replacement_cost_gbp),0) AS cost
       FROM main.dim_asset
       WHERE year(install_date) + expected_life_years BETWEEN 2026 AND 2030
       GROUP BY 1 ORDER BY 1"""
)
st.bar_chart(renew, x="renewal_year", y="cost")

st.subheader("Method note")
st.markdown(
    "SLA targets are illustrative config (P1 1d, P2 5d, P3 10d, P4 20d). "
    "The planted B012 boiler and 2025-Q4 PPM drop belong to the default "
    "profile; see `docs/findings.md`. See `methodology.md` for definitions."
)
