# P09 SPEC (copy of docs/specs section - traceability)

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
