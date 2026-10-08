# P16 wireframe — Energy exceptions (1 page + drill-through, synthetic)

Footer on every page: *"Synthetic data for portfolio demonstration. Savings are
estimates with a stated ±25% band, attributed only to flagged fault modes."*
Slicers global: building, fault type (from `fct_finding`), source profile.

## Page 1 — Energy exceptions (purpose: which meters do we fix first?)

```
+---------------------------------------------------------------+
| KPI cards: Meters With Findings % | Attributed £/yr |            |
| Attributed kWh/yr | Attributed kgCO2e/yr | Meter Faults            |
+---------------------------------------------------------------+
| Bar (top 10): meter by Attributed £/yr, sorted desc,            |
|  data labels on, conditional format: >£5k dark, else grey         |
|  (source: validation/v01_action_list.sql)                        |
+-------------------------------+-----------------------------------+
| Donut: findings by fault     | Table: meter | types | peak |       |
| type (fct_finding)            | £/yr | kWh/yr | kgCO2e | lo/hi    |
|                               | (validation/v02_scorecard.sql)     |
+-------------------------------+-----------------------------------+
| Card: Top 3 Cost Concentration % (how concentrated the money is) |
+---------------------------------------------------------------+
| Tooltip on the bar: [Finding Rank], [Is Step Change],             |
|  Savings Low/High kWh/yr                                        |
| Drill-through: meter evidence page (below)                       |
```

## Page 2 (drill-through) — Meter evidence (purpose: why is this meter listed?)

```
+---------------------------------------------------------------+
| Header: building + meter_id, card row with the meter's          |
|  attributed £/yr and the fault labels it triggered              |
+---------------------------------------------------------------+
| Embed the generated evidence plot from                           |
|  outputs/reports/<BUILDING>.html as an image (or link to it)   |
+---------------------------------------------------------------+
| Small table: finding type -> detector -> first flag timestamp   |
|  (from the per-building JSON; no time series in the model)      |
+---------------------------------------------------------------+
```

Notes for the builder:

- The model is one row per meter, not a time series, so there is no line chart
  here. The evidence plot is the time series — link or embed it rather than
  trying to build a fake trend from totals.
- Do not add a £/m² visual here. P16 has no floor-area join; a per-m² column
  without a sourced denominator would be a fabricated ratio.
- `Meter Faults` (flatline) and `missing_data` meters deliberately show £0.
  Leave the zeros visible: a stuck meter with £0 is the honest output, and
  hiding it would suggest the tool mis-ranked it.