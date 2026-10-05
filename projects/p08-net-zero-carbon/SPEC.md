# P08 SPEC (copy of docs/specs/02-dashboards-p06-p10.md section � traceability)

## P08: Net Zero & carbon

**Location:** `projects/p08-net-zero-carbon/`
**Criteria:** E5, D5, D7, D8
**Business questions:** Are we on the pathway to our target? Which buildings drive emissions? Where is energy wasted outside occupied hours? What would a 10% baseload cut deliver?

### Inputs
`fct_energy_daily, fct_meter_hh, dim_building (GIA), weather (HDD), dim_emission_factor`.

> **Emission factors:** download the current DESNZ/DEFRA GHG conversion factors workbook from gov.uk with a script; load electricity and natural gas factors into `dim_emission_factor` (factor, unit, year, scope, source URL, retrieved date). Never hard-code values from memory. Include a test that the factor year exists for every reporting year used and a documented fallback rule if a year is missing.

### Calculations (document in `methodology.md`, referencing the GHG Protocol scopes and stating boundaries, exclusions and limitations)
- kWh by fuel; **Scope 1** (gas combustion) and **Scope 2** location-based (electricity); a market-based placeholder with a configurable supplier factor (clearly marked as illustrative).
- Intensity: kWh/m² and kgCO₂e/m² (GIA); weather-normalised gas using degree days.
- Baseline year vs current; rolling 12 months; **target pathway** (configurable base year, end year and shape, default linear to net zero) and variance to pathway.
- Overnight baseload (minimum 00:00-05:00 load) as % of daily peak per building.
- What-if parameters: baseload reduction %, heating setpoint change (simple degree-day sensitivity, state assumptions), grid factor change.

### Pages
1. Pathway & KPIs; 2. Building league table (top emitters, intensity quartiles); 3. Energy profile explorer (daily/hourly, weather overlay); 4. Out-of-hours waste; 5. Scenario planner.

### Planted findings
B007 overnight baseload; B019 summer heating.

### Acceptance
- Hand-checked fixture: 1 meter, 1 month, known factor → expected kgCO₂e (test).
- Validation SQL for pathway variance and intensity.
- The two planted findings are the top two items on the "out-of-hours waste" page (document filters).
- `methodology.md` reviewed against the GHG Protocol corporate standard's scope definitions (cite source URL).

---
