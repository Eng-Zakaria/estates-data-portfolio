# DATA.md — provenance

> Rule: every external dataset, standard, code list or conversion factor gets an entry here. Foundation uses **no external data**.

| Name | URL | Licence | Version/year | Retrieved | Used for |
|---|---|---|---|---|---|
| (foundation) | — | — | — | — | Foundation `campus_synth` is 100% synthetic (numpy RNG + Faker names only). No standards codes, factors or rules are embedded. |
| DESNZ/DEFRA GHG conversion factors (flat-format workbook) | https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025 (workbook: https://assets.publishing.service.gov.uk/media/6846b6ea57f3515d9611f0dd/ghg-conversion-factors-2025-flat-format.xlsx) | Open Government Licence v3.0 | 2025 | 2026-10-05 (re-fetched live by `platform/dbt/scripts/fetch_desnz.py`; byte-identical to committed seed) | P04 `dim_emission_factor` seed: electricity 0.177, natural gas 0.2027 kgCO2e/kWh. Factors extracted by script from the official workbook, never typed from memory. |

## Planned external sources (later projects, not yet fetched)

- Uniclass 2015 tables, NBS (P13).
- COBie spec, buildingSMART + UK BIM Framework (P12).
- ISO 19650 UK National Annex / UK BIM Framework guidance (P14).
- HESA EMR spec + TRAC guidance (P10).
- Building Data Genome Project 2 (P16).
- OpenStreetMap footprints, ODbL (P19).
- GHG Protocol Corporate Standard scope definitions (P08 methodology).
