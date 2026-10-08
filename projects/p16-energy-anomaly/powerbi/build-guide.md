# P16 build guide (Power BI Desktop, ~1–2 hours)

## 0. Prerequisites

- `projects/p16-energy-anomaly/outputs/building_scorecard.parquet` and
  `anomalies.parquet`. Generate them with `make eval` (~2 min) — no network,
  no BDG2 download needed.
- Power BI Desktop, and this folder's `theme.json`.
- Parquet is supported natively in current Power BI Desktop (no ODBC driver
  needed); if your build refuses it, convert once with
  `python -c "import pandas as pd; pd.read_parquet('.../building_scorecard.parquet').to_csv('.../building_scorecard.csv', index=False)"`.

## 1. Build order

1. Import the theme. Create a `P16Folder` parameter (text, default
   `projects/p16-energy-anomaly/outputs`, relative to the .pbix location), then
   add the three queries: `building_scorecard.pq` → rename to
   `mart_energy_exceptions`; `anomalies.pq` → `fct_meter_anomaly`;
   `fct_finding.pq` (depends on `mart_energy_exceptions`).
2. Model view: relationships per `model.md` (many-to-one, single direction).
   Rename columns for the report: `peak` → `Peak kWh/period`,
   `types` → `Fault types`, `kwh_year` → `Attributed kWh/yr`,
   `gbp_year` → `Attributed £/yr`, `kgco2e_year` → `Attributed kgCO₂e/yr`.
   Hide `source` after adding it as a slicer.
3. Paste `measures.dax` into a `_measures` table. Apply the format strings in
   the comments — the £/kWh columns must not show raw decimals.
4. Build page 1 and the drill-through page per `wireframe.md`. Add the
   synthetic-data footer (and the ±25% band note) as a text box on each page.
5. Save the .pbix **outside the repo** (it is a large binary and this repo does
   not commit .pbix files).

## 2. Validation checklist (small + default-cache profile, seed 7)

| Check | Expected | Source |
|---|---|---|
| Meters analysed | 18 | `mart_energy_exceptions` row count |
| Rank 1 | M-B007-E01, B007, £7,817.23, 27,918.7 kWh | `validation/v02_scorecard.sql` |
| Rank 2 | M-B019-G01, B019, £815.37, 2,912.0 kWh | `v02` |
| Rank 3 | M-B008-E01, B008, £87.03, 310.8 kWh | `v02` |
| Implied tariff on any row | 0.28 £/kWh | `v02` |
| Clean meter (M-B001-E01) | kWh 0.0, £ 0.00 | `v02` |
| B007 overnight ratio | ≥ 0.55 of peak | `v01`, `v04` |
| M-B015-E01 | flatline label present, £ 0 | `v04` |
| Findings donut total | = number of comma-separated labels in `types` | `v03` |

If `[Top 3 Cost Concentration]` shows roughly 90%, that is expected: savings are
attributed only to flagged meters, so a handful of meters carry the total. Report
it as measured rather than treating it as a bug.

## 3. Screenshots

Human exports page PNGs into `powerbi/screenshots/` (kept empty in the repo).