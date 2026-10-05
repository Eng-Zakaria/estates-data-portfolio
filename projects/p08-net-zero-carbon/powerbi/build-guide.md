# P08 build guide (Power BI Desktop, ~1–3 hours)

## 0. Prerequisites
`data/gold/*.parquet` (run `python projects/p08-net-zero-carbon/scripts/export_gold.py`
after `make dbt-build`), Power BI Desktop, this folder's `theme.json`.

## 1. Build order
1. New report → **Import theme** (`theme.json`).
2. **Get data → Parquet folder**: create a `GoldFolder` text parameter with the
   absolute `data/gold` path; add the five `queries/*.pq` (open each in
   Advanced Editor, set parameter). Rename queries to mart names.
3. **Model view**: check relationships per `model.md`; mark
   `dim_date[date_day]` as *the* date table; hide listed fields.
4. **Measures**: paste `measures.dax` into a `_measures` table (create it via
   Enter Data with one dummy row, then delete the column).
5. **Pages**: build pages 1–5 per `wireframe.md`; add the synthetic-data
   footer textbox to the master/theme layout so it appears on every page.
6. **Parameters**: Baseline Annual kgCO2e (default: last audited year total),
   Target Year (2040), baseload-reduction % (0–30), supplier factor
   (labelled illustrative).
7. Save `.pbix` OUTSIDE the repo (gitignored; >25 MB binaries not committed).

## 2. Validation checklist (small profile, seed 42 — must tie within rounding)

| Check | Expected (from `validation/*.sql`) |
|---|---|
| Scope 1 kWh / kgCO2e | 258,943 / 52,488 (`v01`) |
| Scope 2 kWh / kgCO2e | 609,043 / 107,801 (`v01`) |
| Top intensity building | B007, 1.9872 kgCO2e/m² (`v02`) |
| Top baseload building | B007, 48.8% (`v03`) |
| Summer gas table | empty on small (`v04`); verify on default |
| Monthly carbon bars | Jan/Mar/Feb values in `docs/findings.md` |

## 3. Screenshots
The human exports page PNGs into `powerbi/screenshots/` and links them from
the project README results section.
