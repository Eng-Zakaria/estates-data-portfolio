# PLAN: P16 Energy anomaly and fault detection

## Goal
Detect energy waste/faults on campus HH data (planted B007/B019/M-B015) and open BDG2 hourly data. Honest rules apply (synthetic labels, no accuracy claims on unlabeled data).

## Tasks
1. Scaffold `projects/p16-energy-anomaly/` (self-contained: `src/anomaly/`, `tests/`, `docs/`, `powerbi/`, `Makefile`, `SPEC.md`, `README.md`). No shared-file edits (tree is contested).
2. `data_bdg2.py`: Zenodo DOI 10.5281/zenodo.3887306 (CC-BY 4.0, verified 2026-10-05) zip download w/ md5 + cache; extract metadata + 2-site weather + 20-50 education-building electricity meters; `--synthetic-only` fallback documented.
3. `data_campus.py`: default-profile truth HH + weather (generate via campus_synth if missing; document runtime); small-profile/B007 fast path for tests.
4. `cleaning.py` (gaps/zero/flatline/units/winsorise-fit-only), `baselines.py` (median profile, temp+HoW+holiday regression, GBM; rolling-origin CV; CVRMSE/NMBE), `detectors.py` (MAD z-score, IsolationForest, CUSUM + mean-shift scan, OOH rule), `typology.py` (7 types), `savings.py` (kWh/£/kgCO2e + uncertainty + assumptions; DESNZ seed factors), `evaluate.py` (≥200 injected anomalies → P/R/F1/delay per type/method; planted report; BDG2 top-N review pack, no accuracy claims), `report.py` (Jinja2 HTML + scorecard).
5. Tests: per-detector known-answer fixtures + cleaning/savings math (<60 s).
6. `make eval` end-to-end (both datasets) → metrics JSON → README numbers pasted exactly; B007/B019 in action-list top 3 with savings.
7. `powerbi/` exceptions-page handoff (model/measures/wireframe/validation SQL) feeding P08; `docs/methodology.md`, `docs/bdg2-review.md`, `SPEC.md` copy.
8. Commit on dedicated branch `p16-anomaly` (master is churning); root DATA/STATUS updates deferred to a quiet window and listed in the summary.

## Risks
- 595 MB BDG2 zip (cache + md5; subset extract; synthetic-only fallback).
- Default-profile generation cost for planted B019/M-B015 (document; small-profile B007 path for iteration).
- sklearn IsolationForest runtime on 4.5M rows → evaluate on sampled/aggregated series + per-building parallelism caps; document runtime.
- No `ruptures`: CUSUM + sliding mean-shift scan, documented as such.

## Open questions
- BDG2 site choice (pick 1-2 education-rich sites post-download; record in docs).
- Tariff default (configurable; document assumption, e.g. £0.28/kWh illustrative).
