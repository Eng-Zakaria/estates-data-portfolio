# P07 wireframe — Asset & maintenance (5 pages, synthetic)

Footer on every page: *"Synthetic data for portfolio demonstration."*
Global slicers: building, trade, priority, wo_type.

## Page 1 — Overview (purpose: is the maintenance service healthy?)

```
+--------------------------------------------------------------+
| KPI cards: PPM Completion % | Planned:Reactive | MTTR Days  |
| Total Cost £ | Backlog Count | Repeat Failure Assets         |
+--------------------------------------------------------------+
| Bar: cost by trade (Mechanical/Fabric/Controls/Electrical)   |
+--------------------------------------------------------------+
| Line: PPM completion % by month (Mar dip visible, v05)        |
+--------------------------------------------------------------+
| Donut: condition profile A-D (mart_asset_health)             |
+--------------------------------------------------------------+
```

## Page 2 — Backlog & SLA (purpose: where is the backlog, are we hitting SLA?)

```
+--------------------------------------------------------------+
| Stacked bar: backlog count by age band (0-30/31-90/91-180/180+)|
+--------------------------------------------------------------+
| Table: priority | n_complete | SLA met % | avg days_to_complete|
| Conditional formatting: SLA met < 50% red, >= 90% green       |
+--------------------------------------------------------------+
| Table: oldest 15 open WOs (asset, building, trade, age days) |
+--------------------------------------------------------------+
```

## Page 3 — Asset reliability (purpose: which assets are bad actors?)

```
+--------------------------------------------------------------+
| Pareto: reactive jobs by trade (bar) + cumulative % (line)    |
+--------------------------------------------------------------+
| Bad-actor table (v03): asset | building | type | reactive_12m |
|   | condition | risk | MTBF days | repeat-failure flag        |
| Sort: reactive_12m desc. Top 10 = findings.md list.          |
+--------------------------------------------------------------+
| Decomposition tree: building -> asset_type -> asset           |
+--------------------------------------------------------------+
| Tooltip page: WO history for the asset (raised/completed)    |
+--------------------------------------------------------------+
```

## Page 4 — Lifecycle & renewal forecast (purpose: what must we replace?)

```
+--------------------------------------------------------------+
| Bar: renewal forecast £ by year 2026-2030 (v04)              |
+--------------------------------------------------------------+
| Stacked bar: assets by remaining-life band                   |
|   (over-life / 0-25% / 25-50% / 50-75% / 75-100%)             |
+--------------------------------------------------------------+
| Scatter: criticality (x) vs condition weight (y), size =      |
|   replacement cost, colour = risk band (High/Medium/Low)     |
+--------------------------------------------------------------+
| Table: task templates by asset_type (templates CSV)           |
+--------------------------------------------------------------+
```

## Page 5 — Building drill-through (purpose: one building's story)

```
+--------------------------------------------------------------+
| Drill-through target: dim_building[building_id]              |
| KPI cards (building-scoped): WOs | PPM % | MTTR | cost £     |
+--------------------------------------------------------------+
| Line: monthly WO cost for the building                       |
+--------------------------------------------------------------+
| Table: open backlog for the building (age-sorted)            |
+--------------------------------------------------------------+
| Bookmark: "Reset building" button                            |
+--------------------------------------------------------------+
```
