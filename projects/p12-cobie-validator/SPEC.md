# P12 SPEC (copy of docs/specs section — traceability)

## P12: COBie validator and handover loader

**Location:** `projects/p12-cobie-validator/`
**Criteria:** E2, E6, E7, D3, D6
**Stack:** pandas, openpyxl, Pydantic-style YAML rules, Jinja-free HTML, DuckDB-free file staging, Typer, pytest.
**Goal:** validate a COBie workbook against rules and Asset Information Requirements, then load clean records into the operational asset register with an audit trail.

### Source research (required first step)
Find the public COBie specification (buildingSMART COBie pages and UK BIM Framework guidance): sheet list, column names/order, mandatory columns, keys and relationships. Record URLs/versions in `docs/SOURCES.md`. The sheet set is expected to include Contact, Facility, Floor, Space, Zone, Type, Component, System, Assembly, Connection, Spare, Resource, Job, Impact, Document, Attribute, Coordinate, Issue, Picture, but **verify** and implement what the spec says.

### Inputs
`make_sample_cobie.py` builds a valid workbook for a campus building plus a corrupted variant with ≥ 40 seeded errors across categories (missing sheets/columns, empty mandatory cells, duplicate keys, broken foreign keys, bad email or date formats, invalid category patterns, missing manufacturer/model/warranty/expected-life attributes, duplicate serial numbers).

### Rules engine (`rules/cobie.yml` + `rules/air.yml`)
- Structural rules from the spec: sheets present, columns present and ordered, mandatory fields.
- Keys and referential integrity: Component → Type, Component → Space (including multi-value cells), Space → Floor, System → Component, Job → Type, `CreatedBy` exists in Contact.
- Format rules: email, ISO 8601 dates, numeric ranges, category code pattern (regex; membership check against Uniclass if P13 reference data is available — not available, regex only, stated honestly).
- **AIR rules** (editable YAML simulating an employer's Asset Information Requirements): required attributes per asset class (manufacturer, model, serial, warranty duration, expected life, installation date).

### Outputs
- Validation report (HTML with per-sheet summary and issue table, CSV, JSON). Each issue has sheet, row, column, rule id, severity (blocking / warning), message, suggested fix.
- **Handover readiness score** (weighted completeness) and an exit code ≠ 0 on blocking errors (usable in CI).
- **Handover loader:** maps COBie Type/Component/Space to staging tables → matches to existing assets (serial, IFC GlobalId, or space+type) → `inserted / updated / unchanged / rejected` counts; rejects to quarantine with reasons; load audit table; idempotent re-run; `--dry-run` produces a diff report. Maps COBie category to internal `asset_type`.

### Acceptance
- Every seeded error found with the correct rule id (confusion matrix by error category in README).
- Valid workbook: zero blocking errors.
- Loader is idempotent (second run = all unchanged); rejected rows carry reasons.
- Unit tests for each rule type; AIR change (edit YAML) changes results without code changes.

---
