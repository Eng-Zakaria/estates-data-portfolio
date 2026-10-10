"""Demo pages for the five dashboard projects: P06, P07, P08, P09, P10."""

from __future__ import annotations

from typing import Any

import pandas as pd

from . import data as D
from .base import (
    LEAFLET_CSS,
    LEAFLET_JS,
    bar,
    chart,
    controls,
    grouped_bar,
    heatmap,
    kpi,
    line,
    note,
    pie,
    table,
)
from .catalogue import picker


def _fmt(n: Any, dp: int = 0) -> str:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return str(n)
    return f"{v:,.{dp}f}"


def _safe(df: pd.DataFrame | None, *cols: str) -> pd.DataFrame | None:
    if df is None:
        return None
    missing = [c for c in cols if c not in df.columns]
    return None if missing else df


def _join(df: pd.DataFrame, other: pd.DataFrame | None, keys: list[str],
          cols: list[str]) -> pd.DataFrame:
    """Left-join only columns the left frame does not already have.

    Marts frequently re-declare dimension columns (space_category, nia_m2, ...);
    a plain merge would suffix them to _x/_y and break the page.
    """
    if other is None:
        return df
    have = [c for c in cols if c not in df.columns and c in other.columns]
    if not have:
        return df
    return df.merge(other[keys + have], on=keys, how="left")


# --------------------------------------------------------------------- P06

def space_utilisation():
    util = _safe(D.gold("mart_space_utilisation"), "space_id", "frequency_rate", "occupancy_rate")
    spaces = _safe(D.gold("dim_space"), "space_id", "nia_m2", "space_category")
    depts = _safe(D.gold("dim_department"), "department_id", "staff_fte")
    events = D.gold("fct_timetable_event")
    bldg = _safe(D.gold("dim_building"), "building_id", "building_name")

    if util is None:
        return (
            picker(), "Space utilisation",
            "Frequency × occupancy from the timetable and observed sensor counts.",
            note("`mart_space_utilisation` not found. Run `make dbt-build`."), "",
        )

    df = _join(util, bldg, ["building_id"], ["building_name"])
    df = _join(df, spaces, ["space_id"], ["space_category", "nia_m2", "capacity_seats"])
    df["utilisation"] = df["frequency_rate"] * df["occupancy_rate"]

    booked = float(df["booked_hours"].sum())
    freq = booked / float(df["available_hours"].sum()) if df["available_hours"].sum() else 0.0
    occ = float(df["occupancy_rate"].mean())
    util_pct = freq * occ * 100
    no_show = int((df["occupancy_rate"] < 0.05).sum())
    mismatch = int((df["avg_group_size"] < 0.5 * df["capacity_seats"]).sum()) \
        if "avg_group_size" in df.columns and "capacity_seats" in df.columns else 0

    body = [
        note(
            "<strong>Frequency × occupancy</strong>, the SMG-style definition: timetabled hours ÷ "
            "available hours, multiplied by average attendance ÷ room capacity while in use. "
            "A room can be fully booked and still wasted — that gap is the actionable finding."
        ),
        '<div class="grid g4">',
        kpi(f"{freq*100:.1f}%", "Frequency rate", f"{_fmt(booked)} booked hours"),
        kpi(f"{occ*100:.1f}%", "Occupancy rate", "mean while in use"),
        kpi(f"{util_pct:.1f}%", "Utilisation", "frequency × occupancy"),
        kpi(f"{len(df)}", "Spaces", f"{no_show} near-empty bookings · {mismatch} capacity mismatches"),
        "</div>",
        "<h2>By building</h2>",
    ]

    buildings = sorted(df["building_name"].dropna().unique())
    body.append(controls({"id": "p6-building", "label": "Building",
                          "options": [("all", "All buildings")] + [(b, b) for b in buildings],
                          "default": "all"}))
    grouped = (
        df.groupby("building_name")
          .apply(lambda g: pd.Series({
              "frequency": g["booked_hours"].sum() / max(g["available_hours"].sum(), 1e-9),
              "occupancy": g["occupancy_rate"].mean(),
              "utilisation": (g["booked_hours"].sum() / max(g["available_hours"].sum(), 1e-9))
                             * g["occupancy_rate"].mean(),
          }), include_groups=False)
          .reset_index()
          .sort_values("utilisation")
    )
    body.append(chart(
        "p6-building",
        bar(list(grouped["building_name"]),
            [round(v * 100, 2) for v in grouped["utilisation"]],
            title="Utilisation % by building (frequency × occupancy)",
            y_title="%", horizontal=True),
        tall=True,
    ))

    if events is not None and "start_time" in events.columns:
        ev = events.copy()
        ev["hour"] = pd.to_datetime(ev["start_time"], errors="coerce").dt.hour
        ev = ev.dropna(subset=["hour"])
        if "event_date" in ev.columns:
            ev["dow"] = pd.to_datetime(ev["event_date"], errors="coerce").dt.dayofweek
            grid = ev.groupby(["dow", "hour"]).size().unstack(fill_value=0)
            dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            body.append("<h2>Booking heatmap — when the estate is actually used</h2>")
            body.append(chart(
                "p6-heat",
                heatmap(grid.values.tolist(), list(grid.columns),
                        [dow_names[i] for i in grid.index],
                        title="Booked events by weekday × start hour"),
                tall=True,
            ))

    if spaces is not None and "space_category" in df.columns:
        cat = df.groupby("space_category").apply(
            lambda g: pd.Series({
                "util": (g["booked_hours"].sum() / max(g["available_hours"].sum(), 1e-9))
                        * g["occupancy_rate"].mean(),
                "nia": g["nia_m2"].sum(),
                "n": len(g),
            }), include_groups=False).reset_index().sort_values("util")
        body.append("<h2>By space category</h2>")
        body.append(chart("p6-category",
                          bar(list(cat["space_category"]), [round(v * 100, 2) for v in cat["util"]],
                              title="Utilisation % by category", y_title="%", horizontal=True)))
        body.append(table("p6-cattbl", ["category", "spaces", "NIA m²", "utilisation %"],
                          [[r.space_category, r.n, _fmt(r.nia), f"{r.util*100:.1f}"]
                           for _, r in cat.iterrows()]))

    body.append("<h2>Rooms to review</h2>")
    worst = df.nsmallest(20, "utilisation")
    body.append(note(
        "Lowest-utilisation rooms with their capacity mismatch. Capacity mismatch means average "
        "group size is under half the room's rated capacity — the room is too big for what it is "
        "used for."
    ))
    body.append(table(
        "p6-rooms",
        ["space_id", "building", "category", "NIA m²", "capacity", "events",
         "booked h", "frequency %", "occupancy %", "utilisation %", "avg group"],
        [[r.space_id, r.building_name, r.space_category, _fmt(r.get("nia_m2", "—")),
          r.get("capacity_seats", "—"), r.get("n_events", "—"), _fmt(r.booked_hours),
          f"{r.frequency_rate*100:.1f}", f"{r.occupancy_rate*100:.1f}",
          f"{r.utilisation*100:.2f}",
          r.get("avg_group_size", "—")] for _, r in worst.iterrows()],
    ))

    if depts is not None:
        body.append("<h2>Space per person by department</h2>")
        body.append(note(
            "Department attribution uses the synthetic truth mapping (the gold space dimension does "
            "not yet carry a department key), which is documented in the project README."
        ))
        truth = D.parquet(D.REPO / "data" / "truth" / "spaces.parquet")
        if truth is not None:
            dept_cols = [c for c in truth.columns if "dept" in c.lower()]
            if dept_cols:
                merged = truth.merge(depts, left_on=dept_cols[0], right_on="department_id", how="left")
                alloc = merged.groupby("department_name").agg(
                    nia=("nia_m2", "sum"), staff=("staff_fte", "first")
                ).reset_index()
                alloc = alloc.dropna(subset=["nia"])
                alloc["m2_per_fte"] = alloc["nia"] / alloc["staff"].replace(0, pd.NA)
                med = alloc["m2_per_fte"].median()
                alloc["variance_pct"] = (alloc["m2_per_fte"] / med - 1) * 100
                body.append(chart("p6-dept",
                                  bar(list(alloc["department_name"]),
                                      [round(v, 1) for v in alloc["m2_per_fte"]],
                                      title="NIA m² per staff FTE by department",
                                      y_title="m² / FTE", horizontal=True)))
                body.append(table(
                    "p6-depttbl",
                    ["department", "NIA m²", "staff FTE", "m² per FTE", "vs median"],
                    [[r.department_name, _fmt(r.nia), _fmt(r.staff),
                      f"{r.m2_per_fte:.1f}",
                      (f"+{r.variance_pct:.0f}%", "warn") if r.variance_pct > 20
                      else (f"{r.variance_pct:.0f}%", "ok")] for _, r in alloc.iterrows()],
                ))

    js = """
      (function(){
        var sel = document.getElementById('p6-building');
        if (!sel) return;
        sel.addEventListener('change', function(){
          var rows = document.querySelectorAll('#p6-rooms tbody tr');
          var v = sel.value;
          var shown = 0;
          rows.forEach(function(tr){
            var b = tr.cells[1] ? tr.cells[1].innerText : '';
            var show = (v === 'all') || (b === v);
            tr.style.display = show ? '' : 'none';
            if (show) shown++;
          });
          var cap = document.getElementById('p6-filtered');
          if (cap) cap.textContent = shown + ' of ' + rows.length + ' rooms shown';
        });
      })();
    """
    body.append('<div class="note" id="p6-filtered">Use the building filter to narrow the rooms table.</div>')
    return (
        picker(),
        "P06 · Space utilisation",
        "Frequency × occupancy across the estate, with the capacity-mismatch story underneath.",
        "\n".join(body),
        js,
    )


# --------------------------------------------------------------------- P07

def assets_maintenance():
    wo = _safe(D.gold("fct_work_order"), "wo_id", "wo_type", "priority", "status")
    health = _safe(D.gold("mart_asset_health"), "asset_id", "condition_grade", "risk_score")
    trade = _safe(D.gold("dim_trade"), "trade_id", "trade")

    if wo is None:
        return (picker(), "P07 · Assets & maintenance",
                "Backlog, SLA, reliability and lifecycle from CAFM-style work orders.",
                note("`fct_work_order` not found. Run `make dbt-build`."), "")

    open_wo = wo[wo["is_open"].astype(bool)] if "is_open" in wo.columns else wo
    total_cost = float(wo["cost_gbp"].sum())
    ppm = int((wo["wo_type"] == "PPM").sum()) if "wo_type" in wo.columns else 0
    reactive = int((wo["wo_type"] == "Reactive").sum()) if "wo_type" in wo.columns else 0
    ppm_pct = ppm / len(wo) * 100 if len(wo) else 0

    body = [
        note(
            "Backlog, SLA attainment, reliability and lifecycle from a synthetic CAFM export. "
            "SLA targets are illustrative config (P1 1d, P2 5d, P3 10d, P4 20d) — the gold schema "
            "carries no SLA table, which is stated plainly in the project methodology."
        ),
        '<div class="grid g4">',
        kpi(_fmt(len(wo)), "Work orders", f"{len(open_wo)} open"),
        kpi(f"£{_fmt(total_cost)}", "Total cost", "labour + parts, synthetic"),
        kpi(f"{ppm_pct:.1f}%", "Planned (PPM) share", f"{ppm} planned vs {reactive} reactive"),
        kpi(_fmt(len(health)) if health is not None else "—", "Assets", "condition + criticality scored"),
        "</div>",
        "<h2>Backlog</h2>",
    ]

    if "days_to_complete" in wo.columns:
        dtc = pd.to_numeric(wo["days_to_complete"], errors="coerce").dropna()
        if len(dtc):
            bands = {
                "0–30 days": int(((dtc >= 0) & (dtc <= 30)).sum()),
                "31–90 days": int(((dtc > 30) & (dtc <= 90)).sum()),
                "91–180 days": int(((dtc > 90) & (dtc <= 180)).sum()),
                "180+ days": int((dtc > 180).sum()),
            }
            body.append(chart("p7-ages", pie(list(bands), list(bands.values()),
                                            title="Backlog age bands (days to complete)")))
            body.append(table("p7-agetbl", ["band", "work orders"],
                              [[k, _fmt(v)] for k, v in bands.items()]))

    body.append("<h2>SLA and priority</h2>")
    if "priority" in wo.columns:
        prio = wo.groupby("priority").agg(
            n=("wo_id", "count"),
            cost=("cost_gbp", "sum"),
            mean_days=("days_to_complete", "mean"),
        ).reset_index().sort_values("priority")
        sla = {"P1": 1, "P2": 5, "P3": 10, "P4": 20}
        prio["sla_met"] = [
            ("met" if (r.get("mean_days") or 0) <= sla.get(r["priority"], 99) else "missed",
             "ok" if (r.get("mean_days") or 0) <= sla.get(r["priority"], 99) else "bad")
            for _, r in prio.iterrows()
        ]
        body.append(chart("p7-prio",
                          grouped_bar(list(prio["priority"]),
                                      {"work orders": list(prio["n"]),
                                       "cost £": [round(c) for c in prio["cost"]]},
                                      title="Volume and cost by priority",
                                      y_title="count / £")))
        body.append(table("p7-priotbl",
                          ["priority", "work orders", "cost £", "mean days", "vs SLA target"],
                          [[r.priority, _fmt(r.n), f"£{_fmt(r.cost)}",
                            f"{(r.mean_days or 0):.1f}", r.sla_met]
                           for _, r in prio.iterrows()]))

    body.append("<h2>Cost by trade</h2>")
    trade_col = "trade" if "trade" in wo.columns else None
    if trade_col:
        tc = wo.groupby(trade_col).agg(n=("wo_id", "count"), cost=("cost_gbp", "sum")).reset_index()
        tc = tc.sort_values("cost", ascending=False)
        body.append(chart("p7-trade",
                          bar(list(tc[trade_col]), [round(c) for c in tc["cost"]],
                              title="Cost by trade", y_title="£", horizontal=True, color="#57d9a3")))
        body.append(table("p7-tradetbl", ["trade", "work orders", "cost £"],
                          [[r[trade_col], _fmt(r.n), f"£{_fmt(r.cost)}"] for _, r in tc.iterrows()]))

    if health is not None and len(health):
        body.append("<h2>Asset condition and risk</h2>")
        cond = health["condition_grade"].value_counts().reindex(list("ABCD"), fill_value=0)
        body.append(chart("p7-cond", bar(list(cond.index), list(cond.values),
                                        title="Assets by condition grade", y_title="assets")))
        if "remaining_life_pct" in health.columns:
            rl = pd.to_numeric(health["remaining_life_pct"], errors="coerce").dropna()
            if len(rl):
                body.append(chart(
                    "p7-life",
                    {"data": [{"type": "histogram", "x": list(rl), "xbins": {"size": 5},
                               "marker": {"color": "#b98cff"}}],
                     "layout": {"title": "Remaining life % across the asset register",
                                "paper_bgcolor": "#16212c", "plot_bgcolor": "#16212c",
                                "font": {"color": "#e8eef4"},
                                "xaxis": {"title": "remaining life %", "gridcolor": "#2a3a4a"},
                                "yaxis": {"title": "assets", "gridcolor": "#2a3a4a"}}}))
        if "risk_score" in health.columns:
            top = health.nlargest(15, "risk_score")
            body.append("<h3>Bad actors — highest criticality × condition risk</h3>")
            cols = [c for c in ["asset_id", "building_id", "asset_type", "condition_grade",
                                "criticality", "age_years", "remaining_life_pct",
                                "reactive_12m", "is_repeat_failure", "risk_score"] if c in top.columns]
            body.append(table("p7-bad", cols, [list(r) for _, r in top.iterrows()]))

    if "contractor" in wo.columns:
        body.append("<h2>Contractor spend</h2>")
        con = wo.groupby("contractor").agg(n=("wo_id", "count"), cost=("cost_gbp", "sum")).reset_index()
        con = con.nlargest(12, "cost")
        body.append(chart("p7-contractor",
                          bar(list(con["contractor"]), [round(c) for c in con["cost"]],
                              title="Top contractors by cost", y_title="£", horizontal=True)))
        body.append(table("p7-contractortbl", ["contractor", "work orders", "cost £"],
                          [[r.contractor, _fmt(r.n), f"£{_fmt(r.cost)}"] for _, r in con.iterrows()]))
    return (
        picker(),
        "P07 · Assets & maintenance",
        "Where the backlog is, which assets are bad actors, and what a 5-year renewal looks like.",
        "\n".join(body),
        "",
    )


# --------------------------------------------------------------------- P08

def net_zero_carbon():
    energy = _safe(D.gold("fct_energy_daily"), "meter_id", "utility", "kwh", "hdd")
    monthly = _safe(D.gold("mart_carbon_monthly"), "month", "fuel", "kwh", "kgco2e")
    factors = _safe(D.gold("dim_emission_factor"), "fuel", "factor_kgco2e_per_kwh")
    bldg = _safe(D.gold("dim_building"), "building_id", "gia_m2", "building_name")

    if energy is None or factors is None:
        return (picker(), "P08 · Net zero & carbon",
                "Scope 1/2, intensity, pathway variance and overnight baseload.",
                note("Gold energy marts not found. Run `make dbt-build`."), "")

    fac = dict(zip(factors["fuel"], factors["factor_kgco2e_per_kwh"]))
    energy = energy.copy()
    energy["kgco2e"] = energy.apply(
        lambda r: r["kwh"] * fac.get(r["utility"], 0.0), axis=1
    )
    scope1_fuels = {"gas"}
    energy["scope"] = energy["utility"].map(
        lambda u: "Scope 1 (gas)" if str(u).lower() in scope1_fuels else "Scope 2 (electricity)"
    )

    s1 = energy[energy["scope"].str.startswith("Scope 1")]
    s2 = energy[energy["scope"].str.startswith("Scope 2")]
    per_building = energy.groupby(["meter_id", "building_id", "scope"], as_index=False).agg(
        kwh=("kwh", "sum"), kgco2e=("kgco2e", "sum"))
    if bldg is not None:
        per_building = _join(per_building, bldg, ["building_id"], ["building_name", "gia_m2"])
        per_building["intensity"] = per_building["kgco2e"] / per_building["gia_m2"].replace(0, pd.NA)
        per_building = per_building.dropna(subset=["intensity"])

    body = [
        note(
            "Scope 1 (gas combustion) and Scope 2 location-based (electricity) from half-hourly "
            "meter data, converted with the <strong>DESNZ 2025 factors fetched by script</strong> "
            "— never typed from memory. Market-based Scope 2 is a labelled placeholder and is never "
            "mixed into these totals."
        ),
        '<div class="grid g4">',
        kpi(f"{_fmt(s1['kwh'].sum())} kWh", "Scope 1 energy", f"{_fmt(s1['kgco2e'].sum())} kgCO₂e"),
        kpi(f"{_fmt(s2['kwh'].sum())} kWh", "Scope 2 energy", f"{_fmt(s2['kgco2e'].sum())} kgCO₂e"),
        kpi(f"{_fmt(energy['kgco2e'].sum())}", "Total kgCO₂e", "location-based"),
        kpi(f"{len(factors)}", "Conversion factors", "DESNZ 2025, OGL v3.0"),
        "</div>",
        "<h2>Emission factors in use</h2>",
        body_table_factors(factors),
        "<h2>Carbon by building</h2>",
    ]

    top = per_building.nlargest(20, "kgco2e")
    body.append(chart("p8-buildings",
                      bar([f"{r.building_name} ({r.scope.split()[1]})" for _, r in top.iterrows()],
                          [round(r.kgco2e, 1) for _, r in top.iterrows()],
                          title="kgCO₂e by building and scope", y_title="kgCO₂e",
                          horizontal=True), tall=True))
    if "intensity" in per_building.columns and len(per_building):
        inten = per_building.nlargest(20, "intensity")
        body.append(chart("p8-intensity",
                          bar([f"{r.building_name} ({r.scope.split()[1]})" for _, r in inten.iterrows()],
                              [round(r.intensity, 4) for _, r in inten.iterrows()],
                              title="Carbon intensity kgCO₂e/m² (by GIA)", y_title="kgCO₂e/m²",
                              horizontal=True, color="#57d9a3"), tall=True))
        body.append(table("p8-inttbl",
                          ["building", "scope", "kgCO₂e", "GIA m²", "kgCO₂e/m²"],
                          [[r.building_name, r.scope, _fmt(r.kgco2e, 1),
                            _fmt(r.gia_m2), f"{r.intensity:.4f}"] for _, r in inten.iterrows()]))

    if monthly is not None and len(monthly):
        body.append("<h2>Monthly carbon and pathway variance</h2>")
        body.append(note(
            "Mart baselines are NULL because no base-year data exists, so the pathway uses a "
            "user-supplied baseline rather than a fabricated one. Variance to baseline is shown "
            "exactly as the mart computes it."
        ))
        body.append(chart("p8-monthly",
                          grouped_bar(list(monthly["month"]),
                                      {"kWh": [round(v) for v in monthly["kwh"]],
                                       "kgCO₂e": [round(v, 1) for v in monthly["kgco2e"]]},
                                      title="Energy and emissions by month", y_title="kWh / kgCO₂e")))
        cols = [c for c in ["month", "fuel", "kwh", "kgco2e", "baseline_kwh",
                            "variance_to_baseline"] if c in monthly.columns]
        body.append(table("p8-monthtbl", cols, [list(r) for _, r in monthly.iterrows()]))

    hh = D.gold("fct_meter_hh")
    if hh is not None and "ts_utc" in hh.columns:
        hh = hh.copy()
        hh["ts"] = pd.to_datetime(hh["ts_utc"], errors="coerce", utc=True)
        hh = hh.dropna(subset=["ts"])
        hh["hour"] = hh["ts"].dt.hour
        profile = hh.groupby("hour")["value_kwh"].mean()
        body.append("<h2>Overnight baseload</h2>")
        body.append(note(
            "Baseload is the minimum 00:00–05:00 load as a share of the daily peak. "
            "This is the single most actionable number for a net-zero programme: "
            "it is energy that is being paid for and not used."
        ))
        body.append(chart("p8-profile", line(list(profile.index), [round(v, 3) for v in profile],
                                            title="Mean half-hourly load by hour of day (all meters)",
                                            y_title="kWh"), tall=True))
        base = float(profile.reindex(range(0, 6)).mean())
        peak = float(profile.max())
        body.append('<div class="grid g4">')
        body.append(kpi(f"{base:.3f} kWh", "Mean overnight load", "00:00–05:59"))
        body.append(kpi(f"{peak:.3f} kWh", "Mean daily peak", "busiest half-hour"))
        body.append(kpi(f"{base/peak*100:.1f}%" if peak else "—", "Baseload ratio", "overnight ÷ peak"))
        body.append(kpi(f"{_fmt(len(hh))}", "Half-hourly readings", "DST-correct UTC"))
        body.append("</div>")

    if "hdd" in energy.columns:
        hdd = energy.groupby("energy_date")["hdd"].first().sort_index()
        body.append(chart("p8-hdd", line(list(hdd.index), [round(v, 2) for v in hdd],
                                         title="Heating degree days (weather normalisation)",
                                         y_title="HDD", color="#ffb454")))
        body.append(note(
            "HDD normalisation is indicative only: the synthetic window is a single quarter, so the "
            "weather signal is weak. The methodology states the linear assumption and its limits."
        ))
    return (
        picker(),
        "P08 · Net zero & carbon",
        "Scope 1/2 accounts, intensity league table, pathway variance and overnight baseload.",
        "\n".join(body),
        "",
    )


def body_table_factors(factors: pd.DataFrame) -> str:
    return table(
        "p8-factors",
        [c for c in ["fuel", "scope", "unit", "factor_kgco2e_per_kwh", "factor_year"] if c in factors.columns],
        [[r.get("fuel"), r.get("scope"), r.get("unit"), r.get("factor_kgco2e_per_kwh"),
          r.get("factor_year")] for _, r in factors.iterrows()],
        caption="Sourced from the official DESNZ workbook by "
                "<code>platform/dbt/scripts/fetch_desnz.py</code>.",
    )


# --------------------------------------------------------------------- P09

def compliance():
    status = _safe(D.gold("mart_compliance_status"), "inspection_id", "status", "risk_score")
    types = _safe(D.gold("dim_inspection_type"), "inspection_type_id", "inspection_name",
                  "frequency_months")
    remedial = D.gold("remedial_actions")
    bldg = _safe(D.gold("dim_building"), "building_id", "building_name")

    if status is None:
        return (picker(), "P09 · Compliance tracker",
                "Statutory inspection status, risk, trend and a weekly digest.",
                note("`mart_compliance_status` not found. Run `make dbt-build`."), "")

    df = _join(status, types, ["inspection_type_id"], ["inspection_name", "frequency_months"])
    df = _join(df, bldg, ["building_id"], ["building_name"])

    counts = df["status"].value_counts()
    overdue = int(counts.get("Overdue", 0))
    body = [
        note(
            "Status logic is a single tested view: <em>Compliant · Due ≤ 30 days · Overdue · "
            "Failed – remedial open · No record</em>, with days overdue and a risk score of "
            "criticality × overdue band × failure flag. Boundary cases (due today, due in exactly "
            "30 days, completed late, failed then re-passed) each have a unit test."
        ),
        '<div class="grid g4">',
        kpi(len(df), "Inspections", "small profile, 5 types × 8 buildings"),
        kpi(overdue, "Overdue", f"{counts.get('Failed - remedial open', counts.get('Failed – remedial open', 0))} with open remedial"),
        kpi(int(counts.get("Compliant", 0)), "Compliant", f"{counts.get('Due ≤ 30 days', 0)} due within 30 days"),
        kpi(len(remedial) if remedial is not None else "—", "Remedial actions", "tracked with ageing"),
        "</div>",
        "<h2>Status mix</h2>",
        body.append if False else None,
    ]
    body.append(chart("p9-status", pie(list(counts.index), list(counts.values),
                                      title="Inspections by status")))
    body.append(table("p9-statustbl", ["status", "inspections"],
                      [[k, _fmt(v)] for k, v in counts.items()]))

    body.append("<h2>RAG matrix — inspection type × building</h2>")
    if "inspection_name" in df.columns:
        piv = df.pivot_table(index="inspection_name", columns="building_name",
                             values="status", aggfunc="first")
        rag = {"Compliant": 0, "Due ≤ 30 days": 1, "No record": 2,
               "Failed - remedial open": 3, "Overdue": 3}
        z = [[rag.get(v, 2) for v in row] for row in piv.values]
        body.append(chart(
            "p9-rag",
            {"data": [{"type": "heatmap", "z": z,
                       "x": [str(c) for c in piv.columns],
                       "y": [str(i) for i in piv.index],
                       "colorscale": [[0, "#57d9a3"], [0.5, "#ffb454"], [1, "#ff6b6b"]],
                       "hovertemplate": "%{y} / %{x}<extra></extra>",
                       "text": [[str(v) for v in row] for row in piv.values],
                       "texttemplate": "%{text}",
                       "textfont": {"size": 10}}],
             "layout": {"title": "Red = overdue or failed · Amber = due soon · Green = compliant",
                        "paper_bgcolor": "#16212c", "plot_bgcolor": "#16212c",
                        "font": {"color": "#e8eef4"},
                        "margin": {"l": 170, "r": 20, "t": 45, "b": 60}}},
            tall=True))

    body.append("<h2>Overdue and at-risk inspections</h2>")
    at_risk = df[df["status"].astype(str).str.contains("Overdue|Failed", regex=True)]
    cols = [c for c in ["inspection_id", "building_name", "inspection_name", "due_date",
                        "completed_date", "result", "status", "days_overdue", "risk_score"] if c in df.columns]
    body.append(table("p9-overdue", cols, [list(r) for _, r in at_risk.iterrows()]))

    if remedial is not None and len(remedial):
        body.append("<h2>Remedial action ageing</h2>")
        rem = remedial.copy()
        if "opened_date" in rem.columns and "closed_date" in rem.columns:
            opened = pd.to_datetime(rem["opened_date"], errors="coerce")
            closed = pd.to_datetime(rem["closed_date"], errors="coerce")
            rem["age_days"] = (closed.fillna(pd.Timestamp("2026-03-31")) - opened).dt.days
            rem["still_open"] = closed.isna()
            body.append(chart("p9-remedial",
                              bar(list(rem["remedial_id"]), list(rem["age_days"]),
                                  title="Days open per remedial action", y_title="days",
                                  color="#ff6b6b")))
            rcols = [c for c in ["remedial_id", "inspection_id", "building_id", "opened_date",
                                 "closed_date", "age_days", "still_open", "description",
                                 "contractor", "estimated_cost_gbp"] if c in rem.columns]
            body.append(table("p9-remtbl", rcols, [list(r) for _, r in rem.iterrows()]))

    body.append("<h2>Upcoming due dates</h2>")
    if "due_date" in df.columns:
        due = df[["inspection_id", "building_name", "inspection_name", "due_date", "status"]] \
            if "inspection_name" in df.columns else df[["inspection_id", "building_name", "due_date", "status"]]
        body.append(table("p9-due", list(due.columns), [list(r) for _, r in due.iterrows()]))
    return (
        picker(),
        "P09 · Compliance tracker",
        "Statutory inspection compliance with tested status logic, risk scoring and a weekly digest.",
        "\n".join(x for x in body if x is not None),
        "",
    )


# --------------------------------------------------------------------- P10

def institutional_return():
    out = D.REPO / "data" / "p10_output"
    areas = D.csv(out / "building_areas_2026-03-31.csv")
    costs = D.csv(out / "cost_allocation_2026-03-31.csv")
    energy = D.csv(out / "energy_2026-03-31.csv")
    emissions = D.csv(out / "emissions_2026-03-31.csv")
    validation = D.yaml_file(out / "validation_2026-03-31.yaml")
    mapping = D.csv(out / "category_mapping.csv")

    if areas is None:
        return (picker(), "P10 · Institutional return",
                "A mock HESA EMR / TRAC-style return: mapping, validation, allocation, audit trail.",
                note("`data/p10_output/` not found. Run `make p10-run`."), "")

    body = [
        note(
            "<strong>This is not an official return.</strong> It is a mock built from public HESA EMR "
            "and TRAC guidance, using generic categories where the full coding manual was not "
            "accessible. The point is the process: mapping, building, validating, allocating and "
            "auditing a statutory-style return from gold marts."
        ),
    ]

    if mapping is not None and len(mapping):
        body.append("<h2>Mapping layer — internal category → return category</h2>")
        body.append(note("Versioned config. A test asserts every internal category maps exactly once."))
        body.append(table("p10-mapping", list(mapping.columns),
                          [list(r) for _, r in mapping.iterrows()]))

    if areas is not None and len(areas):
        body.append("<h2>Building floor areas</h2>")
        num_cols = [c for c in areas.columns if areas[c].dtype.kind in "if"]
        agg = {c: "sum" for c in num_cols if "m2" in c.lower() or "area" in c.lower()}
        if not agg:
            agg = {c: "sum" for c in num_cols[:2]}
        totals = areas.agg(agg) if agg else None
        body.append('<div class="grid g4">')
        body.append(kpi(len(areas), "Buildings reported"))
        for col in agg:
            body.append(kpi(_fmt(totals[col]) if totals is not None else "—",
                            col.replace("_", " ")))
        if validation:
            body.append(kpi(_fmt(validation.get("summary", {}).get("blocking", 0))
                            if isinstance(validation, dict) else "—", "Blocking violations"))
        body.append("</div>")
        if "space_category" in areas.columns and any("m2" in c.lower() for c in areas.columns):
            m2col = next(c for c in areas.columns if "m2" in c.lower())
            cat = areas.groupby("space_category")[m2col].sum().sort_values(ascending=False)
            body.append(chart("p10-areas", bar(list(cat.index), [round(v) for v in cat.values],
                                              title=f"Total {m2col} by space category",
                                              y_title=m2col)))
        body.append(table("p10-areatbl", list(areas.columns), [list(r) for _, r in areas.iterrows()]))

    if costs is not None and len(costs):
        body.append("<h2>TRAC-style cost allocation</h2>")
        body.append(note(
            "Cost pools allocated to Teaching / Research / Other using space-based drivers "
            "(NIA × category weighting × department activity split). A test asserts the allocated "
            "total equals the pool total to the penny and that no allocation is negative."
        ))
        target = next((c for c in costs.columns if "teaching" in c.lower()), None)
        if target:
            body.append(chart("p10-costs",
                              grouped_bar(list(costs.iloc[:, 0]),
                                          {c: [round(v) for v in costs[c]]
                                           for c in costs.columns
                                           if c != costs.columns[0] and costs[c].dtype.kind in "if"},
                                          title="Cost by activity", y_title="£")))
        body.append(table("p10-costtbl", list(costs.columns), [list(r) for _, r in costs.iterrows()]))

    if energy is not None and len(energy):
        body.append("<h2>Energy by fuel</h2>")
        body.append(table("p10-energytbl", list(energy.columns),
                          [list(r) for _, r in energy.iterrows()]))
    if emissions is not None and len(emissions):
        body.append("<h2>Emissions</h2>")
        body.append(table("p10-emtbl", list(emissions.columns),
                          [list(r) for _, r in emissions.iterrows()]))

    if validation is not None:
        body.append("<h2>Validation engine</h2>")
        body.append(note(
            "Rules run completeness, valid codes, arithmetic (NIA ≤ GIA, category sums), energy "
            "reconciliation to meter totals and year-on-year change flags. Severity is "
            "<em>blocking</em> or <em>query</em>, mirroring a submitter's validation report."
        ))
        body.append("<pre style=\"background:#16212c;border:1px solid #2a3a4a;border-radius:10px;"
                    "padding:14px;overflow:auto;font-size:12px\">"
                    f"{D.json_file(out / 'validation_2026-03-31.yaml') or ''}</pre>"
                    if False else "")
        body.append(table("p10-validation", ["rule", "severity", "message", "records"],
                          validation_rows(validation)))
    return (
        picker(),
        "P10 · Institutional return",
        "A mock HESA EMR / TRAC-style statutory return built from gold marts, with validation and audit.",
        "\n".join(x for x in body if x),
        "",
    )


def validation_rows(validation: Any) -> list[list[Any]]:
    """Normalise the validation YAML into table rows regardless of its shape."""
    if validation is None:
        return []
    if isinstance(validation, dict):
        for key in ("violations", "issues", "checks", "results"):
            if isinstance(validation.get(key), list):
                items = validation[key]
                break
        else:
            summary = validation.get("summary")
            rows = [[k, str(v), "aggregate", ""] for k, v in (summary or {}).items()]
            return rows
    elif isinstance(validation, list):
        items = validation
    else:
        return []

    rows = []
    for item in items[:200]:
        if isinstance(item, dict):
            rows.append([
                item.get("rule_id") or item.get("rule") or item.get("id") or "",
                item.get("severity", ""),
                item.get("message", ""),
                item.get("records", item.get("affected", "")),
            ])
        else:
            rows.append([str(item), "", "", ""])
    return rows


PAGES = {
    "space-utilisation": space_utilisation,
    "assets-maintenance": assets_maintenance,
    "net-zero-carbon": net_zero_carbon,
    "compliance": compliance,
    "institutional-return": institutional_return,
}