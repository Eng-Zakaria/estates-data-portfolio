"""TRAC-style estates cost allocation (P10) — pools → Teaching/Research/Other.

Simplified driver: NIA × category weighting × department activity split.
Checks: allocated total = pool total (to the penny), no negative allocations.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

# Cost pools (synthetic, derived from work orders + rates proxy)
POOLS = {
    "rates": {"total_gbp": 1_200_000, "description": "Business rates"},
    "utilities": {"total_gbp": 800_000, "description": "Electricity, gas, water"},
    "maintenance": {"total_gbp": 1_500_000, "description": "Work order costs + planned"},
    "cleaning": {"total_gbp": 600_000, "description": "Cleaning contracts"},
    "security": {"total_gbp": 400_000, "description": "Security contracts"},
}

# Category weights for allocation (illustrative)
CATEGORY_WEIGHTS = {
    "Teaching": 1.0,
    "Research": 1.2,  # labs cost more
    "Residential": 0.8,
    "Other": 0.5,
}

# Activity split by department (Teaching/Research/Other fractions)
DEPT_ACTIVITY = {
    "D-ENG": {"teaching": 0.3, "research": 0.7, "other": 0.0},
    "D-PHY": {"teaching": 0.2, "research": 0.8, "other": 0.0},
    "D-HUM": {"teaching": 0.6, "research": 0.3, "other": 0.1},
    "D-MED": {"teaching": 0.3, "research": 0.6, "other": 0.1},
    "D-BUS": {"teaching": 0.5, "research": 0.2, "other": 0.3},
    "D-LAW": {"teaching": 0.7, "research": 0.1, "other": 0.2},
}


def build_allocation() -> pd.DataFrame:
    """Compute allocation of each pool to Teaching/Research/Other."""
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    # Building NIA by return category (join truth spaces parquet for department_id)
    from mapping import INTERNAL_TO_RETURN
    import pyarrow.parquet as pq
    truth_spaces = pq.read_table('data/truth/spaces.parquet').to_pandas()
    truth_spaces = truth_spaces[['space_id', 'department_id']]
    
    space_sql = """
    SELECT s.space_id, s.building_id, s.space_category, s.nia_m2
    FROM main.dim_space s
    """
    spaces = con.execute(space_sql).fetchdf()
    spaces = spaces.merge(truth_spaces, on='space_id', how='left')
    spaces["return_category"] = spaces["space_category"].map(INTERNAL_TO_RETURN)

    # Weighted NIA by building × category
    spaces["weighted_nia"] = spaces["nia_m2"] * spaces["return_category"].map(CATEGORY_WEIGHTS)

    # Department activity split
    spaces["teaching_frac"] = spaces["department_id"].map(lambda d: DEPT_ACTIVITY.get(d, {}).get("teaching", 0))
    spaces["research_frac"] = spaces["department_id"].map(lambda d: DEPT_ACTIVITY.get(d, {}).get("research", 0))
    spaces["other_frac"] = spaces["department_id"].map(lambda d: DEPT_ACTIVITY.get(d, {}).get("other", 0))

    # Weighted NIA by activity
    spaces["teaching_nia"] = spaces["weighted_nia"] * spaces["teaching_frac"]
    spaces["research_nia"] = spaces["weighted_nia"] * spaces["research_frac"]
    spaces["other_nia"] = spaces["weighted_nia"] * spaces["other_frac"]

    # Total drivers
    total_teaching = spaces["teaching_nia"].sum()
    total_research = spaces["research_nia"].sum()
    total_other = spaces["other_nia"].sum()

    # Allocate each pool
    rows = []
    for pool_name, pool_info in POOLS.items():
        pool_total = pool_info["total_gbp"]
        teaching_share = total_teaching / (total_teaching + total_research + total_other)
        research_share = total_research / (total_teaching + total_research + total_other)
        other_share = total_other / (total_teaching + total_research + total_other)

        # Round to pence, adjust last to make sum exact
        teaching_amt = round(pool_total * teaching_share, 2)
        research_amt = round(pool_total * research_share, 2)
        other_amt = round(pool_total - teaching_amt - research_amt, 2)

        rows.append({
            "pool": pool_name,
            "activity": "Teaching",
            "allocated_gbp": teaching_amt,
            "driver_total": total_teaching,
        })
        rows.append({
            "pool": pool_name,
            "activity": "Research",
            "allocated_gbp": research_amt,
            "driver_total": total_research,
        })
        rows.append({
            "pool": pool_name,
            "activity": "Other",
            "allocated_gbp": other_amt,
            "driver_total": total_other,
        })

    con.close()
    return pd.DataFrame(rows)


def check_balance(alloc: pd.DataFrame) -> tuple[bool, list[str]]:
    """Verify each pool sums to its total (to the penny), no negatives."""
    errors = []
    for pool_name, pool_info in POOLS.items():
        pool_alloc = alloc[alloc["pool"] == pool_name]
        total = pool_alloc["allocated_gbp"].sum()
        expected = pool_info["total_gbp"]
        if abs(total - expected) > 0.01:
            errors.append(f"Pool {pool_name}: allocated {total:.2f} != expected {expected:.2f}")
        if (pool_alloc["allocated_gbp"] < 0).any():
            errors.append(f"Pool {pool_name}: negative allocation found")
    return len(errors) == 0, errors


def write_allocation_csv(alloc: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    alloc.to_csv(out_path, index=False)