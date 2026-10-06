"""Return builder: building-level areas, energy, emissions, water, other sections (P10).

Output: Excel workbook, CSV sheets, HTML pack. All synthetic.
"""

from __future__ import annotations

import hashlib
import subprocess
from datetime import date
from pathlib import Path

import duckdb


def build_return(return_date: date, out_dir: Path) -> dict:
    """Build return from gold marts; return manifest with file paths + hashes."""
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    # 1. Space areas by return category (via mapping)
    from mapping import INTERNAL_TO_RETURN

    space_sql = """
    SELECT s.building_id, s.space_category, s.nia_m2, b.gia_m2
    FROM main.dim_space s
    JOIN main.dim_building b USING (building_id)
    """
    spaces = con.execute(space_sql).fetchdf()
    spaces["return_category"] = spaces["space_category"].map(INTERNAL_TO_RETURN)

    # Building-level areas
    bldg_areas = spaces.groupby(["building_id", "return_category"]).agg(
        nia_m2=("nia_m2", "sum")
    ).reset_index()
    # Add GIA per building (once)
    gia = spaces.drop_duplicates("building_id")[["building_id", "gia_m2"]]
    bldg_areas = bldg_areas.merge(gia, on="building_id")
    # Deterministic ordering
    bldg_areas = bldg_areas.sort_values(["building_id", "return_category"]).reset_index(drop=True)

    # 2. Energy by fuel per building
    energy_sql = """
    SELECT d.building_id, d.utility, SUM(d.kwh) AS kwh
    FROM main.fct_energy_daily d
    GROUP BY d.building_id, d.utility
    """
    energy = con.execute(energy_sql).fetchdf()
    energy = energy.sort_values(["building_id", "utility"]).reset_index(drop=True)

    # 3. Emissions
    carbon = energy.copy()
    ef = con.execute("SELECT fuel, factor_kgco2e_per_kwh FROM main.dim_emission_factor").fetchdf()
    fuel_map = {"electricity": "electricity", "gas": "natural_gas"}
    carbon["fuel_mapped"] = carbon["utility"].map(fuel_map)
    carbon = carbon.merge(ef, left_on="fuel_mapped", right_on="fuel")
    carbon["kgco2e"] = carbon["kwh"] * carbon["factor_kgco2e_per_kwh"]
    carbon = carbon.groupby(["building_id", "fuel"])["kgco2e"].sum().reset_index()
    carbon = carbon.sort_values(["building_id", "fuel"]).reset_index(drop=True)

    # 4. Water: not in HH feeds → NA
    # 5. Cost pools (from work orders + synthetic rates)
    cost_sql = """
    SELECT d.building_id, d.trade, SUM(d.cost_gbp) AS cost_gbp
    FROM main.fct_work_order d
    JOIN main.dim_trade t ON LOWER(REPLACE(d.trade, ' ', '_')) = t.trade_id
    GROUP BY d.building_id, d.trade
    """
    costs = con.execute(cost_sql).fetchdf()
    costs = costs.sort_values(["building_id", "trade"]).reset_index(drop=True)

    con.close()

    # Write outputs
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"files": [], "return_date": return_date.isoformat()}

    # Excel workbook (one sheet per section)
    import openpyxl
    wb = openpyxl.Workbook()

    # Sheet 1: Building areas
    ws = wb.active
    ws.title = "Building_Areas"
    ws.append(["building_id", "return_category", "nia_m2", "gia_m2"])
    for _, row in bldg_areas.iterrows():
        ws.append([row["building_id"], row["return_category"], round(row["nia_m2"], 1), round(row["gia_m2"], 1)])

    # Sheet 2: Energy
    ws2 = wb.create_sheet("Energy")
    ws2.append(["building_id", "utility", "kwh"])
    for _, row in energy.iterrows():
        ws2.append([row["building_id"], row["utility"], round(row["kwh"], 1)])

    # Sheet 3: Emissions
    ws3 = wb.create_sheet("Emissions")
    ws3.append(["building_id", "fuel", "kgco2e"])
    for _, row in carbon.iterrows():
        ws3.append([row["building_id"], row["fuel"], round(row["kgco2e"], 1)])

    # Sheet 4: Water (NA)
    ws4 = wb.create_sheet("Water")
    ws4.append(["building_id", "water_m3", "note"])
    for bldg in bldg_areas["building_id"].unique():
        ws4.append([bldg, "NA", "Not in HH meter feeds"])

    # Sheet 5: Costs
    ws5 = wb.create_sheet("Costs")
    ws5.append(["building_id", "trade", "cost_gbp"])
    for _, row in costs.iterrows():
        ws5.append([row["building_id"], row["trade"], round(row["cost_gbp"], 2)])

    # Sheet 6: Validation summary
    ws6 = wb.create_sheet("Validation")
    ws6.append(["rule_id", "message", "severity", "affected_records"])
    # Validation will be run separately; this is a placeholder

    xlsx_path = out_dir / f"return_{return_date.isoformat()}.xlsx"
    wb.save(xlsx_path)

    # CSV extracts (one per sheet)
    for name, df in [
        ("building_areas", bldg_areas),
        ("energy", energy),
        ("emissions", carbon),
        ("costs", costs),
    ]:
        csv_path = out_dir / f"{name}_{return_date.isoformat()}.csv"
        df.to_csv(csv_path, index=False)
        manifest["files"].append({"path": str(csv_path), "sha256": _sha256(csv_path)})

    manifest["files"].append({"path": str(xlsx_path), "sha256": _sha256(xlsx_path)})

    # HTML pack
    html_path = out_dir / f"return_pack_{return_date.isoformat()}.html"
    _write_html_pack(html_path, bldg_areas, energy, carbon, costs, return_date)
    manifest["files"].append({"path": str(html_path), "sha256": _sha256(html_path)})

    return manifest


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_html_pack(path: Path, areas, energy, carbon, costs, return_date: date) -> None:
    total_nia = areas["nia_m2"].sum()
    total_gia = areas.drop_duplicates("building_id")["gia_m2"].sum()
    total_elec = energy[energy["utility"] == "electricity"]["kwh"].sum()
    total_gas = energy[energy["utility"] == "gas"]["kwh"].sum()
    total_co2 = carbon["kgco2e"].sum()

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Institutional Return {return_date}</title>
<style>body{{font-family:Arial,sans-serif;margin:20px;}} table{{border-collapse:collapse;width:100%;margin-bottom:20px;}} th,td{{border:1px solid #ddd;padding:6px;}} th{{background:#f0f0f0;}} .note{{color:#666;font-size:0.9em;}}</style>
</head><body>
<h1>Institutional Return Pack — {return_date}</h1>
<p class="note">Synthetic data for portfolio demonstration. Not an official return.</p>

<h2>Summary</h2>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total NIA (m²)</td><td>{total_nia:,.1f}</td></tr>
<tr><td>Total GIA (m²)</td><td>{total_gia:,.1f}</td></tr>
<tr><td>Electricity (kWh)</td><td>{total_elec:,.1f}</td></tr>
<tr><td>Gas (kWh)</td><td>{total_gas:,.1f}</td></tr>
<tr><td>CO₂e (kg)</td><td>{total_co2:,.1f}</td></tr>
</table>

<h2>Building Areas by Return Category</h2>
<table><tr><th>Building</th><th>Category</th><th>NIA (m²)</th><th>GIA (m²)</th></tr>
""" + "".join(
        f"<tr><td>{r.building_id}</td><td>{r.return_category}</td><td>{r.nia_m2:.1f}</td><td>{r.gia_m2:.1f}</td></tr>"
        for _, r in areas.iterrows()
    ) + f"""
</table>

<h2>Energy by Building & Fuel</h2>
<table><tr><th>Building</th><th>Utility</th><th>kWh</th></tr>
""" + "".join(
        f"<tr><td>{r.building_id}</td><td>{r.utility}</td><td>{r.kwh:.1f}</td></tr>"
        for _, r in energy.iterrows()
    ) + f"""
</table>

<h2>Emissions by Building & Fuel</h2>
<table><tr><th>Building</th><th>Fuel</th><th>kgCO₂e</th></tr>
""" + "".join(
        f"<tr><td>{r.building_id}</td><td>{r.fuel}</td><td>{r.kgco2e:.1f}</td></tr>"
        for _, r in carbon.iterrows()
    ) + f"""
</table>

<h2>Costs by Building & Trade</h2>
<table><tr><th>Building</th><th>Trade</th><th>Cost (GBP)</th></tr>
""" + "".join(
        f"<tr><td>{r.building_id}</td><td>{r.trade}</td><td>{r.cost_gbp:.2f}</td></tr>"
        for _, r in costs.iterrows()
    ) + """
</table>

<p class="note">Water: Not in HH meter feeds. Costs from work orders (synthetic). Mapping illustrative only.</p>
</body></html>"""
    path.write_text(html, encoding="utf-8")