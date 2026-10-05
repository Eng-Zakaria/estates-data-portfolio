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
    - GX resolved for P03: `great-expectations==1.23.2` API verified empirically
      2026-10-05 (pandas runtime batches, suites, ValidationDefinition.run,
      Data Docs); evidence in `docs/PLAN_P03.md`.

## P01 rework candidate (found while building P03, 2026-10-05 — human decision needed)
11. **CAFM ISO datetimes systematically quarantined (P01 `dates.py`)**: the
    foundation generator intentionally emits three `Raised`/`Completed` formats
    (`exports.py:89-101`: `%d/%m/%Y %H:%M` 40%, ISO `t.isoformat()` 30%,
    `%d-%b-%y %H:%M` 30%), but `platform/src/ingest/dates.py CANDIDATES` has no
    timezone-aware ISO candidate (`%Y-%m-%dT%H:%M:%S%z`). Measured on the small
    profile (seed 42): 1,798/6,039 raw CAFM rows (29.8%) carry ISO `+00:00`
    stamps; 1,785 valid rows sit in quarantine as
    `future_dates:unparseable_raised`. Silver CAFM is therefore missing ~30% of
    legitimate work orders, which flows into P04 `fct_work_order` and P07.
    One-line fix + `make ingest` re-run + P01/P04 acceptance refresh would
    resolve it, but that churns silver while P04 is in flight — left for the
    human to schedule. P03 check `cafm_quarantine_explained_rate` (warn)
    tracks it.

## P04 follow-ups (done 2026-10-05; first jobs for P02/P05)
- Default (full-volume) profile `dbt build` runtime/memory not yet measured (small profile: ~19 s, green).
- DESNZ factors are single-year (2025); add a factor-year coverage test + fallback rule when multi-year reporting lands (P08).
- Upstream caveat: per §11 above, silver CAFM is missing ~30% of legitimate work orders; P04 `fct_work_order` faithfully reproduces silver (4,171 → 4,171, §4 of `docs/ACCEPTANCE_P04.md`) but inherits the gap until the P01 fix lands.
