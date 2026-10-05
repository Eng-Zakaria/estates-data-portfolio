# P09 build guide (Power BI Desktop, ~1–3 hours)

## 0. Prerequisites
`data/gold/*.parquet` + `remedial_actions.parquet` (run
`python projects/p09-compliance-tracker/scripts/gen_remedial.py` after
`make dbt-build`), Power BI Desktop, this folder's `theme.json`.

## 1. Build order
1. Import theme. Create `GoldFolder` parameter → add `.pq` queries per
   `model.md` (add `fct_inspection.pq`, `remedial_actions.pq`,
   `dim_inspection_type.pq`, `dim_building.pq`, `dim_date.pq`,
   `dim_asset.pq` following the P08/P06 pattern).
2. Model view: relationships per `model.md`; mark `dim_date[date_day]`;
   hide internals.
3. Paste `measures.dax` into a `_measures` table.
4. Add calculated column `RAG Status` on `fct_inspection` per `measures.dax`.
5. Build pages 1–5 per `wireframe.md` + synthetic-data footer everywhere.
6. Save `.pbix` OUTSIDE the repo (gitignored).

## 2. Validation checklist (small profile, seed 42)

| Check | Expected (from `validation/*.sql`) |
|---|---|
| Total inspections | 40 (`v01`) |
| Overdue | ~15 (verify `v02`) |
| Failed + remedial open | 2 (planted) |
| Remedial >90 days | 2 (planted) |
| Trend months | 12 (`v05`) |

## 3. Screenshots
Human exports page PNGs into `powerbi/screenshots/`.