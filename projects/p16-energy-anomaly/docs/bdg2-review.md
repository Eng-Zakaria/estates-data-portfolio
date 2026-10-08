# P16 BDG2 review pack (public data, no labels, no accuracy claimed)

## What this is, and what it is not

The Building Data Genome Project 2 release is real, public, hourly meter data.
It has **no fault labels**, so nothing in this section is a measurement of
accuracy. This is a *review queue*: the pipeline's heuristic flags ranked 50
education buildings, the top 6 got evidence pages for a human to check. Every
number is reported as computed, with its assumptions, and none of it should be
quoted as a real-world saving.

## Data actually used

| Field | Value |
|---|---|
| DOI | https://doi.org/10.5281/zenodo.3887306 |
| Licence | CC-BY 4.0 International (checked on the Zenodo record page 2026-10-07) |
| ZIP | 595,266,464 bytes, md5 `44393dc4cf61e84dec105e955368c890` (verified on download) |
| Cadence | hourly, 2016–2017 |
| Buildings | 50 education buildings with electricity meters, at the 2 education-richest sites |
| Sites | Rat (US/Eastern, 25 buildings), Lamb (Europe/London, 25) |
| Weather | the release's own site weather CSV, localised to UTC the same way as the meters |

Selection rule (`data_bdg2.select_subset`): buildings whose
`primaryspaceusage` contains "education" **and** that have a non-null
`electricity` flag **and** an actual column in `electricity_cleaned.csv`, then
the top 2 sites by count, capped at 25 per site. Selection reads the zip's
`metadata.csv` and the electricity table header; it never hard-codes a building
name.

Timezone handling: release timestamps are site-local naive. They are localised
with the metadata timezone (`ambiguous="NaT"`, `nonexistent="shift_forward"`) and
converted to UTC, so ambiguous autumn hours are dropped and nonexistent spring
hours are shifted — never invented. This is covered by
`tests/test_loaders.py::test_load_bdg2_subset_localises_to_utc_and_drops_ambiguous`.

## Findings, as measured

Ranked by total flags (drift weighted up, since a sustained shift matters more
than a spike). Costs are USD at an illustrative **$0.15/kWh** — a placeholder
for US commercial pricing, not a sourced tariff. **No CO₂ is reported**: UK DESNZ
grid factors (0.177 kgCO₂e/kWh) do not apply to the US or Irish grids these two
sites sit on, and applying them would produce a confident wrong number.

| Rank | Building | Site | Flags | Fault labels | Attributed kWh/yr | Illustrative $/yr |
|---|---|---|---|---|---|---|
| 1 | Lamb_education_Alina | Lamb | 17,246 | flatline, missing_data, step_change | 0.0 | 0.00 |
| 2 | Rat_education_Chance | Rat | 17,068 | flatline, missing_data, step_change | 122.6 | 18.39 |
| 3 | Lamb_education_Camille | Lamb | 16,760 | flatline, step_change | 0.0 | 0.00 |
| 4 | Rat_education_Angelica | Rat | 16,678 | high_overnight_baseload, missing_data, step_change, weekend_operation | 57,406.7 | 8,611.00 |
| 5 | Lamb_education_Eula | Lamb | 16,222 | flatline, gradual_drift, missing_data, spike, step_change | 608.8 | 91.32 |
| 6 | Lamb_education_Freddy | Lamb | 16,197 | flatline, missing_data, step_change | 0.0 | 0.00 |

Reading these honestly:

- **Four of the top six are data-quality problems, not energy problems.** A
  `flatline_meter_fault` label means 48 identical readings; `missing_data` means
  gaps. Both correctly produce £0 attributed savings, because a stuck meter's
  real consumption cannot be estimated from the stuck meter. Ranking them by
  flag count therefore surfaces meter hygiene before energy waste — defensible,
  but it means "top 6 by flags" is not "top 6 by savings".
- **Flag counts are huge (16k–17k periods out of ~17,500 hourly periods).** At
  this flag density the ranking is dominated by CUSUM saturation on long,
  gappy series: once the accumulator trips it stays tripped. Read the counts as
  "this meter needs a human", not as a severity score.
- **Only one meter in the top six carries material savings**
  (Rat_education_Angelica, high overnight baseload + weekend operation on an
  education building: 57.4 MWh/yr attributed). That is a plausible pattern for
  the building type, but with no labels it is a hypothesis, not a finding.
- **Thresholds were set on synthetic data.** They are being applied here to a
  completely different population, different grid, different climate and a
  different metering regime. Treat every label as "look at this".

## What a human should do with this pack

1. Open `outputs/bdg2/<building>.html` for each of the six. Each page has the
   series, shaded flat-line spans, MAD spike markers, dashed change-point rules
   and the finding table.
2. Start with the flat-line and missing-data meters: those are meter and comms
   faults. No energy saving can be claimed from them until the meter works.
3. Only then look at the baseload and weekend-operation cases, against occupancy
   and schedule data for that building.
4. Adjudicate the six outcomes and use them as the first labelled test set. That
   is the single highest-value next step for this project, and it is a human
   judgement, not a modelling improvement.

## Reproduce

```bash
PYTHONPATH=projects/p16-energy-anomaly/src python -m anomaly.cli fetch-bdg2     # ~1.2 GB, md5-verified
PYTHONPATH=projects/p16-energy-anomaly/src python -m anomaly.cli review-bdg2    # ~40 min, 50 buildings
```

Runtime note: ~40 minutes for 50 buildings, dominated by the gradient-boosting
baseline fit on ~17,500 hourly rows per meter. The GBM result is kept only for
the CV comparison table; detection uses the regression baseline, which is
milliseconds. Cutting the GBM fit or parallelising per meter is the obvious next
optimisation if this ever runs on a schedule.