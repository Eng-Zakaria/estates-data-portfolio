# P07 build guide (Power BI Desktop, ~1–3 hours)

## 0. Prerequisites
`data/gold/*.parquet` (`python projects/p08-net-zero-carbon/scripts/export_gold.py`
after `make dbt-build`), Power BI Desktop, this folder's `theme.json`.

## 1. Build order
1. Import theme. Create `GoldFolder` parameter → add `.pq` queries per
   `model.md` (`fct_work_order.pq`, `dim_asset.pq`, `mart_asset_health.pq`,
   `dim_building.pq`, `dim_date.pq`, `dim_trade.pq`).
2. Add `task_templates.csv` (from `projects/p07-asset-maintenance/templates/`)
   and an `rlsusers.csv` mapping table (see §3).
3. Model view: relationships per `model.md`; mark `dim_date[date_day]`;
   hide internals. Add calculated columns:
   - `fct_work_order[age_days]` = `DATEDIFF(raised_ts, DATE(2026,3,31), DAY)`
     and `fct_work_order[age_band]` (0-30/31-90/91-180/180+).
   - `dim_asset[renewal_year]` = `YEAR(install_date) + expected_life_years`.
4. Paste `measures.dax` into a `_measures` table.
5. Build pages 1–5 per `wireframe.md` + synthetic-data footer everywhere.
6. Configure RLS roles (§3). Save `.pbix` outside the repo.

## 2. Validation checklist (small profile, seed 42)

| Check | Expected (from `validation/*.sql`) |
|---|---|
| PPM completion | 93.0% (`v01`) |
| Planned : reactive | 1.88 (`v01`) |
| Reactive MTTR | 3.17 days (`v01`) |
| Backlog | 327 open, 323 in 0-30 band (`v02`) |
| SLA met P1 / P2 / P3 / P4 | 23.7% / 65.2% / 85.1% / 97.2% (`v02`) |
| Bad actors top-2 | A-B003-000520 Autoclave (8), A-B006-000970 Pump (8) (`v03`) |
| Repeat-failure assets | 169 (`v03`) |
| Condition A/B/C/D | 288 / 440 / 485 / 283 (`v04`) |
| Renewal forecast 2026-2030 | £2.11M total (~£420k/yr) (`v04`) |
| PPM March completion | 79.4% (`v05`) |
| B012 boiler | 0 rows on small profile — default-profile plant (`v05`) |

## 3. RLS test cases ("View as")

1. Create `rlsusers.csv` with columns `principal,building_id`, e.g.
   `manager.b003@university.example,B003`.
2. Model view → Manage roles → `building_manager` with DAX:
   `dim_building[building_id] IN CALCULATETABLE(VALUES(rlsusers[building_id]), rlsusers[principal] = USERPRINCIPALNAME())`
3. Test: View as `building_manager` → all cards/tables show B003 only;
   totals tie to `v01` filtered to B003. View as `estates_analyst` → all
   8 buildings. Unmapped principal → blank report (expected).
4. Confirm `mart_asset_health` is scoped via the dim_building path (no
   direct filter on the mart).

## 4. Screenshots
Human exports page PNGs into `powerbi/screenshots/`.
