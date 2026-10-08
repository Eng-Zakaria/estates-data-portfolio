# P07 SPEC (copy of docs/specs/02-dashboards-p06-p10.md section - traceability)

## P07: Asset & maintenance performance

**Location:** `projects/p07-asset-maintenance/`
**Criteria:** E5, E6, D5, D7 (CAFM-style data)
**Business questions:** Where is the backlog? Which assets are "bad actors"? What will we need to replace in the next 5 years? Are we doing enough planned maintenance?

### Gold inputs
`fct_work_order, dim_asset, dim_building, dim_date, dim_trade, mart_asset_health`, plus a maintenance-task template library.

> **SFG20 note:** SFG20 is a commercial maintenance specification. Do **not** reproduce its content. Build a small *synthetic, generic* task-template library (for example "AHU quarterly inspection") clearly labelled "SFG20-style generic templates, not SFG20 content", and show how real SFG20 task schedules would link to assets by asset type.

### KPIs
PPM completion %, planned:reactive ratio, backlog count and age bands (0-30 / 31-90 / 91-180 / 180+ days), SLA met % by priority, MTTR, MTBF (assets with ≥ 2 failures), repeat-failure assets (≥ 3 reactive jobs in 12 months), cost per m², cost by trade, condition profile A-D, remaining life % (age ÷ expected life), 5-year renewal forecast (£ by year), criticality × condition risk matrix.

### Pages
1. Overview; 2. Backlog & SLA; 3. Asset reliability (Pareto of fault codes, bad-actor table, decomposition tree); 4. Lifecycle & renewal forecast; 5. Building drill-through (tooltips, bookmarks). Include **row-level security** roles (building manager sees own buildings): document the role DAX and how to test with "View as".

### Planted findings
B012 boiler repeat failures; PPM completion drop in one quarter.

### Acceptance
- Validation SQL for all headline KPIs; fixture tests for MTTR, backlog age banding, and renewal forecast.
- RLS design documented with test cases.
- A "bad actors" top-10 list in `docs/findings.md` showing the planted boiler ranked in the top 3.

---
