# P08 wireframe — Net zero & carbon (5 pages, synthetic)

Footer on every page: *"Synthetic data for portfolio demonstration."*
Slicers global: building, fuel/utility, month. Teaching-week/holiday flags
from dim_date on relevant pages.

## Page 1 — Pathway & KPIs (purpose: are we on track?)

```
+----------------------------------------------------------+
| KPI cards: Total kWh | Scope1 kgCO2e | Scope2 kgCO2e     |
| Emissions intensity kgCO2e/m2 | Variance to pathway %  |
+----------------------------------------------------------+
| Line: monthly kgCO2e by fuel (stacked) + pathway line    |
|  X: mart_carbon_monthly[month]; Y: kgco2e; pathway:      |
|  Baseline-annual param, linear 2024->2040                |
+----------------------------------------------------------+
| Bar: monthly kWh elec vs gas with HDD overlay (line)     |
+----------------------------------------------------------+
```

## Page 2 — Building league table (purpose: who drives emissions?)

```
+----------------------------------------------------------+
| Table sorted by kgCO2e_per_m2 DESC: building | GIA |   |
| kWh | kgCO2e | kWh/m2 | kgCO2e/m2 | heating_fuel          |
| Conditional formatting on intensity (3-colour scale)     |
+----------------------------------------------------------+
| Map/bar: kgCO2e by building (B007 expected top, v02)     |
+----------------------------------------------------------+
```
Tooltip: monthly trend for the hovered building (drill-through to page 3).

## Page 3 — Energy profile explorer (purpose: when is energy used?)

```
+----------------------------------------------------------+
| Line: daily kWh (slicer: building, utility) + HDD line   |
+----------------------------------------------------------+
| Heatmap: day x hour kW from fct_meter_hh (avg)           |
+----------------------------------------------------------+
```

## Page 4 — Out-of-hours waste (purpose: where is energy wasted?)

```
+----------------------------------------------------------+
| Bar: baseload % by building DESC (B007 top 48.4%, v03)   |
| Table: building | overnight_min_kW | peak_kW | baseload% |
+----------------------------------------------------------+
| Table: summer gas kWh/m2 (Jun-Aug; empty on small — v04)  |
|  Default profile: B019 expected top; verify, do not      |
|  assume (see docs/findings.md).                          |
+----------------------------------------------------------+
```

## Page 5 — Scenario planner (purpose: what would X deliver?)

What-if parameters: baseload reduction % (0–30), heating setpoint change
(HDD sensitivity note), grid factor change, baseline-annual + target-year.
Visuals: parameter sliders → saved kWh/kgCO2e cards + revised pathway line.
Market-based supplier factor slider labelled **illustrative** (methodology §5).

Bookmarks: "Small-profile view" (Jan–Mar 2026) vs "Full-year view".
Drill-throughs: building → page 3 filtered; month → page 1 filtered.
