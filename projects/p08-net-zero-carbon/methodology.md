# P08 methodology — net-zero carbon calculations

> **Synthetic data for portfolio demonstration.** Methods below follow public
> standards; all figures in this project are synthetic.

## Standards referenced

- GHG Protocol **Corporate Accounting and Reporting Standard**
  (https://ghgprotocol.org/corporate-standard) — scope definitions:
  Scope 1 = direct emissions from owned/controlled sources (here: gas
  combusted in boilers); Scope 2 = indirect emissions from purchased
  electricity (location-based method used throughout).
- GHG Protocol **Scope 2 Guidance**
  (https://ghgprotocol.org/scope-2-guidance) — location-based reporting uses
  grid-average factors; market-based reporting (supplier-specific) is shown
  only as an illustrative placeholder (see §5).
- Emission factors: DESNZ/DEFRA 2025 conversion factors workbook
  (Open Government Licence v3.0; see root `DATA.md`). Single factor year;
  multi-year reporting needs a year-coverage rule (open question).

## Boundaries and exclusions

- Included: Scope 1 (natural gas, kWh Net CV × DESNZ factor), Scope 2
  location-based (electricity × DESNZ UK factor).
- Excluded: Scope 3 (procurement, travel, waste), refrigerants, oil/LPG,
  water/heat meters (not in the HH feeds), embodied carbon. Biomass/biogas:
  none in the synthetic estate.
- Estate boundary = the 8 synthetic small-profile buildings (B001–B008),
  window 2026-01-01…2026-03-31. No weather-year correction beyond HDD ratio.

## Calculations

1. **Emissions**: `kgCO2e = kWh × factor` per fuel (factors passed in, never
   hard-coded; `src/carbon.py::kwh_to_kgco2e`). Fixture-tested.
2. **Intensity**: value ÷ building GIA (`intensity()`; NULL when GIA ≤ 0).
3. **Weather normalisation (gas)**: degree-day ratio
   `kwh × ref_hdd / hdd` (base 15.5 °C from truth weather). Assumes heating
   load scales linearly with HDD with no baseload split — indicative only;
   with one quarter of data the signal is weak (stated limit).
4. **Pathway**: straight line from base-year annual total to net zero in the
   target year (defaults 2024 → 2040); variance = (actual − pathway)/pathway.
   The synthetic window contains no base-year data, so mart baselines are
   NULL and the dashboard pathway uses a user-supplied baseline parameter
   (build-guide documents the check).
5. **Overnight baseload**: minimum 00:00–05:00 London interval load (kW)
   ÷ daily peak kW × 100, averaged over days (`baseload_pct()`).
6. **Rolling 12 months**: trailing mean (partial windows allowed and labelled).

## Market-based placeholder rule

A supplier-factor parameter may scale Scope 2 for what-if analysis. It must
be labelled **illustrative** in every visual and never reported alongside
location-based totals without that label.
