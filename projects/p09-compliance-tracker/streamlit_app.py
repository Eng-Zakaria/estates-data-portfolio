"""Streamlit mirror of the P09 compliance tracker (synthetic demo).

Run from the repo root:  streamlit run projects/p09-compliance-tracker/streamlit_app.py
Reads gold marts from data/warehouse.duckdb (read-only).
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB = Path("data/warehouse.duckdb")
st.set_page_config(page_title="Compliance tracker (synthetic demo)", layout="wide")
st.title("Compliance tracker — synthetic portfolio demo")
st.caption("Synthetic data for portfolio demonstration.")


@st.cache_data
def q(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


kpi = q(
    """SELECT COUNT(*) n, SUM(CASE WHEN due_date <= DATE '2026-03-31' AND (completed_date IS NULL OR completed_date > due_date) THEN 1 ELSE 0 END) overdue,
              SUM(CASE WHEN result='Fail' AND (SELECT opened_date FROM read_parquet('data/gold/remedial_actions.parquet') r WHERE r.inspection_id=f.inspection_id) IS NOT NULL AND (SELECT closed_date FROM read_parquet('data/gold/remedial_actions.parquet') r WHERE r.inspection_id=f.inspection_id) IS NULL THEN 1 ELSE 0 END) failed_open
       FROM main.fct_inspection f"""
).iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Total inspections", f"{int(kpi['n'])}")
c2.metric("Overdue", f"{int(kpi['overdue'])}")
c3.metric("Failed + remedial open", f"{int(kpi['failed_open'])}")

st.subheader("Overdue list")
overdue = q(
    """SELECT f.inspection_id, f.building_id, i.inspection_name, f.due_date,
              f.completed_date, f.result, r.opened_date AS remedial_opened
       FROM main.fct_inspection f
       JOIN main.dim_inspection_type i USING (inspection_type_id)
       LEFT JOIN read_parquet('data/gold/remedial_actions.parquet') r ON r.inspection_id=f.inspection_id
       WHERE f.due_date <= DATE '2026-03-31' AND (f.completed_date IS NULL OR f.completed_date > f.due_date)
       ORDER BY f.due_date"""
)
st.dataframe(overdue, use_container_width=True)

st.subheader("Remedial ageing")
rem = q(
    """SELECT remedial_id, building_id, opened_date, closed_date,
              (CASE WHEN closed_date IS NOT NULL THEN closed_date - opened_date ELSE DATE '2026-03-31' - opened_date END) AS ageing_days,
              contractor
       FROM read_parquet('data/gold/remedial_actions.parquet')
       ORDER BY ageing_days DESC"""
)
st.dataframe(rem, use_container_width=True)

st.subheader("Method note")
st.markdown(
    "Status logic: Failed+open remedial → Red; Overdue → Red; Due ≤30d → Amber; else Green. "
    "Risk = criticality × overdue_band × failure_flag. See `methodology.md`. "
    "Frequencies are illustrative (see `docs/frequencies.md`)."
)