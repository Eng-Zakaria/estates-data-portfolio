# P16 Power BI model (synthetic campus; BDG2 excluded from the model)

Source: `projects/p16-energy-anomaly/outputs/*.parquet` via `queries/*.pq`
(`P16Folder` parameter). BDG2 numbers stay out of this report on purpose:
they are public, USD-priced, unlabelled review candidates, and mixing them with
synthetic campus £ figures would invite the reader to compare numbers that are
not comparable.

## Tables and columns used

| Query / table name in Power BI | File | Grain | Key columns used |
|---|---|---|---|
| `mart_energy_exceptions` | `building_scorecard.parquet` | meter | meter_id, building, source, peak, types, kwh_year, gbp_year |
| `fct_meter_anomaly` | `anomalies.parquet` | meter | meter_id, building, source, kwh_year, gbp_year, kgco2e_year, kwh_lo, kwh_hi |
| `fct_finding` (derived in Power Query) | from `mart_energy_exceptions` | meter x fault type | meter_id, type, detector, start_ts, kwh_day, cost_year, kgco2e_year |

`types` in the scorecard is a comma-joined string; split it in Power Query
(Table.SplitColumn, delimiter `,`) into `fct_finding[type]` so the page can
count findings by fault type rather than by meter.

Hidden: `source` internals once a slicer exists; `peak` (kWh per period) if you
prefer a £/kWh ratio visual. No RLS (portfolio demo).

## Relationships (single direction, many-to-one)

- fct_meter_anomaly[meter_id] → mart_energy_exceptions[meter_id]
- fct_finding[meter_id] → mart_energy_exceptions[meter_id]

No bidirectional filter: the exceptions page aggregates from meters, and letting
findings filter back would double-count `gbp_year`.

There is no date table relationship. P16 output is one row per meter (whole-series
totals), not a time series, so a date axis would be decorative. Add
`dim_date[date_day]` only if you later import `first_flag_ts` per detector.

## What feeds P08

`fct_meter_anomaly[kgco2e_year]` and `[kwh_year]` are the attribution-ready
columns for the net-zero carbon report. Import them as a page-only table (the
"Energy exceptions" page) rather than adding fault-level carbon into the
headline carbon mart, so a fault estimate can never silently shift a reported
scope 1/2 total. The DESNZ factors behind `kgco2e_year` are the same P04 seed
values P08 uses (electricity 0.177, gas 0.2027 kgCO2e/kWh), so the two pages
reconcile.