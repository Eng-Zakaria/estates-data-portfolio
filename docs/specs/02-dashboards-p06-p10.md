# Dashboard projects P06-P10

All five follow the **Power BI handoff protocol in `AGENTS.md`** (model.md, queries/*.pq, measures.dax, wireframe.md, theme.json, build-guide.md, validation SQL, optional Streamlit mirror). The agent prepares everything; the human builds the visuals in Power BI Desktop and adds screenshots.

Every dashboard README must open with **question → insight → decision** lines, written for a non-technical estates manager. Every page footer says: *"Synthetic data for portfolio demonstration."*

Depends on: foundation + P04 gold marts (or the equivalent gold extracts exported to `data/gold/*.parquet|csv`).

---

## P06: Space utilisation

**Location:** `projects/p06-space-utilisation/`
**Criteria:** E5, E6, D5
**Business questions:** Which rooms are booked but not used? How much space do we have per person by department? How much space could be released at a target utilisation?

### Gold inputs
`dim_space, dim_building, dim_department, dim_date, fct_timetable_event, fct_space_observed_occupancy` (from sensors or survey-style samples; produced with P17 when available, otherwise from the foundation's occupancy model).

### KPIs (SMG-style frequency × occupancy; state the definitions in `methodology.md`)
- **Frequency rate** = timetabled hours ÷ available hours (core window and teaching weeks configurable, default 09:00-18:00 Mon-Fri).
- **Occupancy rate** = average attendance ÷ room capacity while in use.
- **Utilisation** = frequency × occupancy.
- m² NIA per staff FTE / per student FTE; space share by category; cost per m²; **no-show rate** (booked, observed occupancy ≈ 0); **capacity mismatch** (group size < 50% of capacity).

### Pages
1. **Executive overview:** KPI cards, utilisation by building, trend by teaching week.
2. **Heatmap:** day × hour utilisation matrix with building/room-type slicers.
3. **Rooms to review:** table of low-utilisation and high-no-show rooms, conditional formatting, tooltip page with weekly profile, drill-through to a room page.
4. **Department allocation:** m² per FTE vs institutional median (bar + variance), category mix.
5. **What-if:** parameter for target utilisation → estimated rooms/m² releasable.

### DAX measures required (write full DAX in `measures.dax` with comments)
`Available Hours, Timetabled Hours, Frequency %, Avg Occupancy %, Utilisation %, No-show %, NIA m², m² per Staff FTE, m² per Student FTE, Variance to Median, Releasable m² (what-if), Utilisation vs Target`.

### Planted findings to surface
B003 teaching rooms (booked ≥ 70% but occupancy < 30%); department D-ENG ≈ 40% above median m²/FTE.

### Acceptance
- Validation SQL reproduces every headline KPI; values tie to the Power BI numbers within rounding.
- `wireframe.md` specifies all 5 pages in enough detail to build without guessing.
- Unit tests for the KPI SQL on a hand-computed fixture (e.g., one room, 3 events).
- Planted findings are visible in the first two pages (documented with the exact filter to see them).

---

## P07: Asset & maintenance performance

**Location:** `projects/p07-asset-maintenance/`
**Criteria:** E5, E6, D5, D7 (CAFM-style data)
**Business questions:** Where is the backlog? Which assets are "bad actors"? What will we need to replace in the next 5 years? Are we doing enough planned maintenance?

### Gold inputs
`fct_work_order, dim_asset, dim_building, dim_date, dim_trade, mart_asset_health`, plus a maintenance-task template library.

> **SFG20 note:** SFG20 is a commercial maintenance specification. Do **not** reproduce its content. Build a small *synthetic, generic* task-template library (for example "AHU quarterly inspection") clearly labelled "SFG20-style generic templates, not SFG20 content", and show how real SFG20 task schedules would link to assets by asset type.

### KPIs
PPM completion %, planned:reactive ratio, backlog count and age bands (0-30 / 31-90 / 91-180 / 180+ days), SLA met % by priority, MTTR, MTBF (assets with ≥ 2 failures), repeat-failure assets (≥ 3 reactive jobs in 12 months), cost per m², cost by trade, condition profile A-D, remaining life % (age ÷ expected life), 5-year renewal forecast (£ by year), criticality × condition risk matrix.

### Pages
1. Overview; 2. Backlog & SLA; 3. Asset reliability (Pareto of fault codes, bad-actor table, decomposition tree); 4. Lifecycle & renewal forecast; 5. Building drill-through (tooltips, bookmarks). Include **row-level security** roles (building manager sees own buildings): document the role DAX and how to test with "View as".

### Planted findings
B012 boiler repeat failures; PPM completion drop in one quarter.

### Acceptance
- Validation SQL for all headline KPIs; fixture tests for MTTR, backlog age banding, and renewal forecast.
- RLS design documented with test cases.
- A "bad actors" top-10 list in `docs/findings.md` showing the planted boiler ranked in the top 3.

---

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

## P09: Statutory compliance tracker

**Location:** `projects/p09-compliance-tracker/`
**Criteria:** E5, E6, D5, D7
**Business questions:** What is overdue? What is due in the next 90 days and who is doing it? Which failures still have open remedial actions?

### Data and logic
- `dim_inspection_type` with `frequency_months`. The frequencies in the foundation are **illustrative config**; add `docs/frequencies.md` telling the human to verify each against current legal duties and guidance (for example fire alarm servicing, legionella checks, electrical condition reports, gas safety, lifts) before ever using them for real.
- Status logic (single SQL view, tested): `Compliant`, `Due ≤ 30 days`, `Overdue`, `Failed – remedial open`, `No record`. Days overdue; **risk score** = criticality × overdue band × failure flag.
- Monthly compliance snapshots (dbt snapshot or generated history) for trend.
- **Weekly digest automation:** Python + Jinja2 script that renders an HTML compliance digest (overdue, due-soon, remedial ageing) and sends it to Mailpit; scheduled in Airflow (P02) if available.

### Pages
1. Executive RAG matrix (inspection type × building); 2. Overdue list with drill-through to asset/building; 3. Next-90-days calendar and workload by week/contractor; 4. Remedial actions ageing; 5. Compliance trend.

### Acceptance
- Status logic tests with boundary cases (due today, due in 30 days, completed late, failed then re-passed).
- Planted findings visible: legionella-type overdue in 3 buildings; 2 failed inspections with remedial > 90 days.
- Digest renders and validates as HTML; golden-file test.

---

## P10: Mock institutional return (HESA EMR / TRAC-style)

**Location:** `projects/p10-institutional-return/`
**Criteria:** E6, E7 (and the responsibility "institutional returns (e.g. HESA EMR, TRAC)")
**Goal:** demonstrate how estates data becomes a validated, reconciled, auditable statutory-style return, and how estates costs are allocated TRAC-style.

> **Not an official return.** Before coding, read HESA's publicly available Estates Management Record specification/coding manual and the TRAC guidance. Save URLs, versions and retrieval dates in `docs/SOURCES.md`. Align field names and code lists with what is publicly documented. Where you cannot access a source, use generic categories, mark the output *illustrative*, and list the gap in `docs/OPEN_QUESTIONS.md`. Never present invented categories as official.

### Components
1. **Mapping layer:** internal space categories → return categories (versioned config table; test that every internal category maps exactly once).
2. **Return builder:** building-level floor areas by category (GIA/NIA), energy by fuel, emissions, water, and other sections identified from the public spec. Output as an Excel workbook (one sheet per section + a validation sheet), CSV, and an HTML "return pack" summary.
3. **Validation engine** (rules in YAML): completeness; valid codes; arithmetic (NIA ≤ GIA, category sum = NIA ± tolerance); energy reconciliation to meter totals (tolerance %); year-on-year change flags (> ±15% requires an explanation field); cross-field rules. Severity: `blocking` vs `query`. Output mirrors a submitter's validation report (rule id, message, affected records).
4. **Reconciliation & lineage:** each reported figure traces back to model + SQL + row counts + checksum; reconciliation table (reported vs source vs difference). Lineage coverage 100% of reported fields.
5. **TRAC-style estates cost allocation:** cost pools (rates, utilities, maintenance, cleaning, security) allocated to Teaching / Research / Other using space-based drivers (NIA × category weighting × department activity split). Checks: allocated total = pool total (to the penny), no negative allocations. Document the method and its simplifications.
6. **Audit trail:** `audit.run_log` (run_id, git sha, config hash, input data hashes, rule-set version, timestamp), `audit.sign_off` (reviewer, status, comment), immutable return snapshots (Parquet + hash), re-run reproduces identical output hash.
7. Optional Power BI one-pager: return health (blocking/query counts, reconciliation differences).

### Acceptance
- Seeded errors (area mismatch, wrong code, energy mismatch, missing building) are caught with the correct severity.
- Deterministic: two runs on the same inputs produce identical output hashes (test).
- Cost allocation sums exactly to pool totals (test).
- `docs/SOURCES.md` lists every external spec used; README states plainly that this is a mock modelled on public documentation.
