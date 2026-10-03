# OPEN_QUESTIONS.md

## Foundation (non-blocking, assumptions recorded in docs/PLAN.md)
- None blocking. End date fixed at 2026-03-31 for reproducibility.

## Later projects — do not invent, fetch first (human action needed where download is gated)
1. **DESNZ GHG conversion factors** (P04/P08): need official workbook URL + year. Script must download; never hard-code from memory.
2. **Uniclass 2015 tables** (P13): NBS download may require licence acceptance. If gated, use `mock_uniclass_dev_placeholder.csv` (labelled non-authoritative) and refuse final outputs.
3. **COBie spec** (P12): verify sheet list/columns/keys against buildingSMART + UK BIM Framework.
4. **ISO 19650 naming convention** (P14): spec's field pattern is unverified memory — read UK BIM Framework / National Annex first.
5. **Statutory inspection frequencies** (P09): foundation frequencies are illustrative config — verify against legal duties/guidance before real use.
6. **HESA EMR / TRAC** (P10): read public coding manual/guidance; record URLs/versions in `docs/SOURCES.md`.
7. **SFG20** (P07): commercial — do not reproduce; use generic "SFG20-style" templates labelled as such.
8. **BDG2 licence** (P16): verify + record licence; download by script.
9. **CO₂ guideline sources** (P17: 1000/1500 ppm thresholds): verify + cite.
10. **IfcOpenShell / Airflow / GX / dbt / sentence-transformers APIs**: verify against pinned versions' docs before coding those projects.
