# OPEN_QUESTIONS.md

## Foundation (non-blocking, assumptions recorded in docs/PLAN.md)
- None blocking. End date fixed at 2026-03-31 for reproducibility.

## Later projects — do not invent, fetch first (human action needed where download is gated)
1. **DESNZ GHG conversion factors** (P04/P08): need official workbook URL + year. Script must download; never hard-code from memory.
2. **Uniclass 2015 tables** (P13): PARTIALLY RESOLVED 2026-10-08. The NBS download
   (https://uniclass.thenbs.com/download) is login-gated and JS-rendered; an unauthenticated
   script cannot obtain the tables (`projects/p13-uniclass-mapper/scripts/fetch_uniclass.py`
   logs the attempt and falls back). P13 therefore ships
   `projects/p13-uniclass-mapper/data/mock_uniclass_dev_placeholder.csv` (96 rows, every row
   `is_mock=TRUE`), stamps `is_mock` on every output row and refuses `--final` outputs with
   `MockDataError`. **Human action needed:** download the official Products (`Pr_`) and
   Systems (`Ss_`) tables with an NBS account, save as `projects/p13-uniclass-mapper/data/uniclass_2015.csv`,
   then (a) re-check the 1,324 golden-set labels against the real titles, (b) complete the
   human review of `data/review_sample.csv` (265 rows = 20.02%, **0 reviewed so far** — the
   spec requires ≥ 20% reviewed before accuracy is reported), and (c) re-run `make p13-eval`
   so every number in the README is re-measured. Until then the reported accuracy measures
   agreement with synthetic labels, not real-world Uniclass performance.
3. **COBie spec** (P12): RESOLVED 2026-10-06 — sheet set, Component→Type/Space and
   System/Job/Zone FK semantics cross-checked via NBS "What is COBie" + NBIMS
   COBie lineage (direct buildingSMART fetch timed out; recorded honestly in
   `projects/p12-cobie-validator/docs/SOURCES.md`). Column order enforced for
   `Component` only; full per-sheet order matrices still need the employer's template.
4. **ISO 19650 naming convention** (P14): RESOLVED 2026-10-07 for the published edition — CDBB "BIM Toolkit |
   National Annex Guidance" (Tables 1.1–1.5, 2.2) plus UK BIM Framework Guidance Part C Edition 1 were
   read and encoded in `projects/p14-iso19650-checker/conventions/uk_national_annex.yml`; every value is
   quoted in `projects/p14-iso19650-checker/docs/SOURCES.md`. The superseded `uk_example.yml` was deleted.
   Remaining gap: a **2021 update to the UK National Annex** is reported by secondary sources
   (https://www.symetri.us/insights/blog/iso-19650-file-naming-update) to rename the fields to
   *Project – Originator – Functional Breakdown – Spatial Breakdown – Form – Discipline – Number* and to
   revise the discipline code list. That edition was **not obtained**, so it is not encoded; if the human
   can supply it, add it as a third convention file and re-verify Tables 1.3–1.5.
5. **Statutory inspection frequencies** (P09): foundation frequencies are illustrative config — verify against legal duties/guidance before real use.
6. **HESA EMR / TRAC** (P10): read public coding manual/guidance; record URLs/versions in `docs/SOURCES.md`.
7. **SFG20** (P07): commercial — do not reproduce; use generic "SFG20-style" templates labelled as such.
8. **BDG2 licence** (P16): RESOLVED 2026-10-07/08 — Zenodo record 3887306 states Creative Commons
   Attribution 4.0 International; zip md5 `44393dc4cf61e84dec105e955368c890` verified on download and
   recorded in `DATA.md`. Data is fetched by script and cached (never committed).
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

## P16 follow-ups (2026-10-08 — human decision needed)
- **Overnight-baseload threshold does not transfer between profiles** (measured, `scripts/threshold_separation.py`):
  0 false positives on the small profile, **21 of 58** normal electricity meters on the default profile, while the
  planted fault measures only 0.530 (the fault starts 9 months into the series, diluting the whole-series ratio).
  Known fix: compare each meter against its own baseload or its building type's percentile rather than a global
  50%-of-peak cut-off. That needs an estate baseline the synthetic profiles do not provide honestly, and tuning it
  against the same data used for evaluation would invalidate the injection study. Full write-up:
  `projects/p16-energy-anomaly/docs/methodology.md` §3.1.
- **BDG2 review pack needs adjudication.** The top-6 pack has no labels; someone with building knowledge should
  check them. Those six outcomes would be this project's first labelled real-data test set.
- **Tariffs are illustrative placeholders** (£0.28/kWh campus, $0.15/kWh BDG2). Replace with the institution's
  contracted rates before publishing any saving.
- **BDG2 review pass takes ~40 min** for 50 buildings, dominated by the GBM baseline fit whose output is only used
  for the CV comparison table (detection uses the fast regression). Cut or parallelise it if this runs on a schedule.
