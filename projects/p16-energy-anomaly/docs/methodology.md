# P16 methodology (synthetic campus + BDG2 review)

> All campus numbers are synthetic. BDG2 numbers are real meter data with
> heuristic flags for manual review — no accuracy is claimed on BDG2.

## 1. Series and cleaning

Campus: half-hourly kWh per meter (`meter_readings_hh`), UTC, merged with hourly
campus weather (`temp_c`). BDG2: hourly kWh, site-local naive timestamps localised
with the site timezone from BDG2 metadata (Rat US/Eastern, Lamb Europe/London) and
converted to UTC; ambiguous/nonexistent DST times are dropped, never fabricated.

Cleaning flags (never silently dropped for detection): nulls, negatives, zeros,
flat-line runs (48 identical trailing periods ≈ 24 h at HH, 48 h at hourly), and
winsorising at the 1st/99th percentiles **for baseline fitting only**.

## 2. Baselines

Three baselines are fit per meter and compared with rolling-origin CV
(expanding train window, 7-day test chunks, no shuffling), scored with
CVRMSE (RMSE / mean |y|) and NMBE (mean bias / mean |y|):

- (a) median profile by (day-of-week, hour);
- (b) Ridge regression (α = 1.0) on hour, day-of-week, hour-of-week, weekend
  flag and heating-degree-hours (base 15.5 °C) where temperature is available;
- (c) gradient boosting (`HistGradientBoostingRegressor`, `max_iter=200`, fixed seed).

Detection residuals come from (b): the best documented accuracy/cost trade-off
(GBM fits cost ~5 s per meter; regression is instant and within noise of GBM on
these series — CV table in the acceptance doc).

## 3. Detectors and thresholds

| Detector | Rule | Threshold origin |
|---|---|---|
| MAD z-score | \|0.6745·(r−median)/MAD\| > 4 | standard robust gate |
| Isolation Forest | `contamination=0.02` on [hour-sin, hour-cos, dow, residual] | ensemble vote, fixed seed |
| CUSUM | two-sided, drift 1.0, threshold 8.0 | sustained-shift scan |
| Change-point scan | sliding 48-period window means differ by > 6 robust z | step locator |
| Overnight rule | mean(00–05) > x% of 99th-percentile peak | **x = 50**. Separates cleanly on the **small** profile (normal baseload max 0.463, planted fault 0.553: 1 TP, 0 FP of 7 normal electricity meters) but **does not separate on the default profile** (normal max 0.550, planted 0.530 → 1 TP, **21 FP of 58**). Reproduce with `scripts/threshold_separation.py`. See §5.1 — this is the project's biggest open problem |
| Overnight drift | last-28d minus first-28d overnight mean > 8% of peak (and z-significant) | measured on both profiles: normal night-diff/peak max 0.0031 (small) / 0.0094 (default), planted creep 0.128 / 0.130 → 1 TP, **0 FP** on both |
| Flat-line | 48 identical trailing readings | meter-fault signature |
| Missing | null indicator | data-quality flag |

Two corrections found by testing (documented, not hidden):

1. The CUSUM reference (median/scale) is taken from the **leading 25%** of the
   series. A global reference lets a sustained shift occupying much of the window
   drag the reference toward itself and mute detection — the original code missed
   a +8σ step in its own unit test.
2. Series-level drift is tested on **overnight means**, not regression residuals:
   a baseline trained on month 1 develops seasonal bias by month 3–24 that a
   residual first-vs-last test mistakes for meter drift on every meter. Nights
   are occupancy-free, so a rising night mean is a rising baseload by construction.

Overnight/weekend waste patterns apply to **electricity only**: night and weekend
gas use in the heating season is legitimate heating, and the data confirm it
(all small-profile gas meters would otherwise flag permanently).

### 3.1 The overnight threshold does not transfer between profiles

Measured with `scripts/threshold_separation.py` (both profiles, seed 42):

| Profile | Normal electricity overnight ratio | Planted (M-B007-E01) | Flagged at x = 0.50 |
|---|---|---|---|
| small | max 0.463, median 0.382 (7 meters) | 0.553 | 1 TP, 0 FP |
| default | max 0.550, median 0.445 (58 meters) | 0.530 | 1 TP, **21 FP** |

This is a real failure, not a rounding artefact. Two things drive it:

1. **The planted fault is diluted over the series.** The generator applies the
   overnight HVAC fault from 2025-01-01 in a series that starts 2024-04-01, so
   the whole-series overnight/peak ratio lands at 0.530 on the default profile
   versus 0.553 on the small one. The fault itself is 0.6 of peak; the measured
   ratio is an average over faulted and unfaulted months.
2. **Normal baseload varies with profile, not with fault.** On the default
   profile 21 of 58 normal electricity meters sit at 0.52–0.55 of peak. A single
   global "x % of peak" cut-off cannot separate a building whose baseload is
   naturally half its peak from one whose baseload crept there.

The 50%-of-peak rule stays in the pipeline because the action list is reported
per meter with its evidence plot and the label is a *triage* hint, not a claim.
But a correct fix is known and not implemented here: compare each meter's
overnight ratio against **its own** typical baseload (e.g. the median overnight
ratio of its own non-faulted months, or a per-building-type percentile across
the estate) rather than against a global fraction of peak. That needs an estate
baseline the current synthetic profiles do not provide honestly, and re-tuning it
on the test data would defeat the purpose of the injection study. Recorded in
`docs/OPEN_QUESTIONS.md`.

The overnight-**drift** threshold does transfer: 0 FP on both profiles. It is
the more trustworthy of the two waste tests.

## 4. Typology and savings

Labels: `high_overnight_baseload`, `weekend_operation` (electricity only),
`step_change`, `gradual_drift` (overnight-creep test), `spike` (≥ 3 MAD flags),
`flatline_meter_fault`, `missing_data`. The Jan 2–4 change points on
Teaching/Office (not Residential) buildings are the post-New-Year schedule
return — genuine operational steps, kept as `step_change` with £0 attributed
waste (no sustained over-use vs baseline).

Savings are **attributed only to flagged fault modes**: overnight excess for
overnight faults; thresholded positive-residual excess (above 3 robust sd, so
symmetric noise makes no phantom savings — clean gas meters measure £0.4–1.2/yr)
for spike/step/drift; £0 for stuck/gappy meters (use cannot be estimated).
Annualised over series days with a stated ±25% band. Tariff £0.28/kWh
(illustrative, configurable); emission factors DESNZ 2025 via the P04 seed
(electricity 0.177, gas 0.2027 kgCO₂e/kWh; identical fallback when run outside
the repo). Taking the larger of the two excess modes may understate meters with
several independent faults — the conservative direction for a savings claim.

## 5. Evaluation

- **Injection study** (`make eval`): 210 sparse, non-overlapping anomalies (35 per
  type: step, drift, spike, flatline, ooh, missing) injected after a clean
  90-day training window on held-out default-profile meter M-B001-E01; baseline
  fit on clean history (M&V practice). Reported per method: precision, recall,
  F1, mean detection delay. A dense-injection pilot (220 events on 1,440 periods)
  is documented as a negative result: robust scales saturate when the series is
  mostly anomaly, giving recall-1/precision-0 artefacts — hence the sparse design.
- **Planted findings**: B007-E01 (overnight HVAC at 60% of peak) ranks #1,
  M-B019-G01 (5-week summer heating fault) #2 on the 18-meter action list;
  M-B015-E01 5-day flat-line detected with 193/240 flaggable periods (first 48
  form the warm-up window) and change points bracketing the B019 fault
  (2025-07-06 / 2025-08-10 vs planted 07-07→08-10).
- **BDG2**: 50 education buildings (Rat 25, Lamb 25) ranked by flag count; top-6
  evidence pack for manual review. Costs in USD at an illustrative $0.15/kWh;
  **no CO₂ reported** (UK DESNZ factors do not apply to US/IE grids) and **no
  accuracy claimed** (no labels). Details in `bdg2-review.md`.

### 5.2 Threshold transfer check

Beyond the injection study, `scripts/threshold_separation.py` measures the two
waste thresholds against planted vs normal meters on **both** campus profiles.
This is what caught the overnight-threshold failure in §3.1: the action list
looked right because most of it comes from the small profile, and the 21 default-
profile false positives would never have shown up in the top-5 ranking. The check
runs in seconds and should be wired into `make eval` (currently run manually).

## 6. Deliberate stack deviations (spec §P16)

- No `ruptures`: CUSUM + sliding mean-shift scan instead (verified in unit tests).
- No plotly/matplotlib: dependency-free inline-SVG evidence plots (one less heavy
  install; render anywhere).
- `HistGradientBoostingRegressor` from scikit-learn 1.9.0 (pinned-env API:
  `fit/predict` on dense float arrays — verified empirically, not from memory).
