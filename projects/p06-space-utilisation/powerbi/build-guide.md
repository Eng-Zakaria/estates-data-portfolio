# P06 build guide (Power BI Desktop, ~1–3 hours)

## 0. Prerequisites
`data/gold/*.parquet` (`python projects/p08-net-zero-carbon/scripts/export_gold.py`
after `make dbt-build`), Power BI Desktop, this folder's `theme.json`.

## 1. Build order
1. Import theme. Create `GoldFolder` parameter → add `.pq` queries per
   `model.md` (add `mart_space_utilisation.pq`, `fct_timetable_event.pq`,
   `fct_space_observed_occupancy.pq`, `dim_space.pq`, `dim_building.pq`,
   `dim_department.pq`, `dim_date.pq` following the P08 pattern).
2. Model view: relationships per `model.md`; mark `dim_date[date_day]`;
   hide internals. Add calculated column `no_show_flag` per measures.dax.
3. Paste `measures.dax` into a `_measures` table.
4. Build pages 1–5 per `wireframe.md` + synthetic-data footer everywhere.
5. Parameters: target utilisation (40%), teaching-week window. Save `.pbix`
   outside the repo.

## 2. Validation checklist (small profile, seed 42)

| Check | Expected (from `validation/*.sql`) |
|---|---|
| Spaces / timetabled hrs / avail per space | 495 / 24,052 / 576 (`v01`) |
| Frequency / occupancy / utilisation | 8.4% / 15.7% / 4.2% (`v01`) |
| B003 teaching filter (freq ≥ 50%, occ < 30%) | 30 rooms (`v05` closest; ≥70% yields 0 — report measured) |
| No-shows (covered events) | 3 of 3,336 (`v02`); mismatches 6,704 |
| D-ENG m²/staff-FTE vs median | 247.5 vs 64.3, +285% (`v04`) |

## 3. Screenshots
Human exports page PNGs into `powerbi/screenshots/`.
