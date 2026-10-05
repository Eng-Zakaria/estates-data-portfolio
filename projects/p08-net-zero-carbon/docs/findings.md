# P08 findings (small profile, seed 42 — synthetic)

## Planted finding 1: B007 overnight baseload — CONFIRMED

`validation/v03_baseload.sql` ranks B007 first: **48.8%** baseload
(overnight min 37.4 kW vs 76.5 kW peak, 91 days). B007 is also top of the
intensity league (`v02_intensity.sql`: 1.9872 kgCO2e/m², 10.778 kWh/m²).
B007 is an Office building on gas heating — overnight setback/controls
review is the indicated decision. Reproduce: run `v03_baseload.sql`, sort
`baseload_pct DESC`, first row.

Runner-up note: B005 (47.3%) and B001/B003 (≈47.2%) are close behind; the page-4
"top 2" slot should use the measured ranking, currently B007 then B005.

## Planted finding 2: B019 summer heating — NOT VERIFIABLE on small profile

- `dim_building` (small) contains B001–B008 only; **B019 does not exist**.
- Window is Jan–Mar 2026; `validation/v04_summer_gas.sql` (Jun–Aug gas/m²)
  correctly returns **zero rows**.
- For the default profile: run `v04_summer_gas.sql`; the finding predicts
  B019 first. If B019 is still absent/top-ranked differently, record the
  measured result here instead of the prediction. Do not present the
  prediction as a result.

## Headline totals (validation checklist)

- Scope 1: 258,943 kWh → **52,488 kgCO2e**; Scope 2: 609,043 kWh →
  **107,801 kgCO2e** (`v01_scope_totals.sql`). Total ≈ 160,289 kgCO2e.
  (Measured against the current warehouse/gold state; TZ-correct date
  attribution — see `docs/ACCEPTANCE_P04.md` §5 item 6. Re-run validation
  after any P04 meter-model change.)
- Carbon mart cross-check: monthly rows sum to the same scope totals
  (elec 36,858.3 + 33,690.5 + 37,251.8 = 107,800.6 ✓; gas 19,918.3 +
  16,875.0 + 15,694.5 = 52,487.7 ✓).
