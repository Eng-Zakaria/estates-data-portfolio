# P16 SPEC (copy of docs/specs section — traceability)

## P16: Energy anomaly and fault detection

**Location:** `projects/p16-energy-anomaly/`
**Criteria:** E3, E5 (feeds dashboards), D7, D8
**Stack:** Python, pandas, scikit-learn, Jinja2, pytest (no `ruptures`/plotly —
dependency-free CUSUM + change-point scan and inline-SVG plots instead; see README §6).
**Goal:** detect energy waste and meter faults on campus half-hourly data and open
BDG2 hourly data, with honest evaluation and savings estimates.

### Data
1. **Building Data Genome Project 2** (Zenodo DOI 10.5281/zenodo.3887306, CC-BY 4.0
   verified live 2026-10-07; md5-pinned 595 MB zip, download by script, cached in
   `data/` and never committed). Education buildings at the two most
   education-rich sites (Rat, US/Eastern; Lamb, Europe/London), 50 buildings.
2. Campus synthetic half-hourly data with planted anomalies (B007 overnight
   baseload, B019 summer heating, M-B015-E01 flat-line). Small profile carries
   B007 only; B019/M-B015 verified against an isolated default-profile cache
   (`data/p16_default/`, generated on demand, gitignored).

### Pipeline
1. **Cleaning:** gaps, zero runs, flat-lines, unit sanity, outlier winsorising for baseline fitting only.
2. **Baselines:** (a) weekday/hour median profile; (b) regression on outdoor
   temperature (degree-hours), hour-of-week and holiday flags; (c) gradient
   boosting; **rolling-origin time-series cross-validation**; CVRMSE/NMBE fit metrics.
3. **Anomaly detectors:** robust residual z-score (MAD); Isolation Forest on
   engineered features; CUSUM / change-point detection for sustained shifts
   (baseload creep); rule for out-of-hours consumption above x% of peak (x = 50%,
   measured gap — see methodology).
4. **Fault typology:** high overnight baseload, weekend operation, step change,
   gradual drift (overnight-creep test), spike, flat-line/meter fault, missing data.
5. **Savings estimate:** kWh, £ (configurable tariff, £0.28/kWh illustrative),
   kgCO₂e (DESNZ 2025 factors via P04/P08), annualised, ±25% band, assumptions stated.
   Savings are attributed only to flagged fault modes.
6. **Prioritised action list** with evidence plots per finding.

### Evaluation
- 210 sparse, non-overlapping injected anomalies (known type, magnitude,
  duration) on a held-out default-profile meter; precision, recall, F1 and
  detection delay per type and per method. Dense-injection artefact documented
  (robust scales saturate when the series is mostly anomaly).
- For BDG2 (no labels): top-6-by-flags manual-review pack with plots; no accuracy claimed.
- Planted campus findings: B007 #1 and B019 #2 on the action list; M-B015 flat-line
  detected with exact window.

### Outputs
`anomalies.parquet`, `building_scorecard.parquet`, per-building HTML reports with
inline-SVG evidence plots, Power BI handoff for an "Energy exceptions" page (feeds P08).

### Acceptance
- `make eval` reproduces all metrics from fixed seeds; numbers in README exactly as measured.
- Planted B007 and B019 findings are in the top 3 of the action list, with savings estimates.
- Tests for each detector on synthetic series with known answers (e.g. pure step change
  at a known timestamp).

---
