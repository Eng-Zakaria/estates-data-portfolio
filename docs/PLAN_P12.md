# PLAN: P12 COBie validator and handover loader

## Goal
Validate a COBie workbook against rules and AIR, then load clean records into the operational asset register with an audit trail. Rules-driven, idempotent, CI-gateable.

## Tasks
1. Source research: find public COBie spec (buildingSMART + UK BIM Framework). Record sheet list, columns, keys in `docs/SOURCES.md`. Verify against spec, do not invent.
2. Scaffold `projects/p12-cobie-validator/`: `src/`, `tests/`, `docs/`, `rules/`, `Makefile`.
3. `make_sample_cobie.py`: build valid workbook for a campus building + corrupted variant with ≥40 seeded errors (missing sheets/columns, empty mandatory, duplicate keys, broken FKs, bad email/date, invalid category, missing manufacturer/model/warranty/expected-life, duplicate serials).
4. Rules engine `rules/cobie.yml` + `rules/air.yml`: structural (sheets/columns/mandatory), keys + referential integrity (Component→Type, Component→Space including multi-value, Space→Floor, System→Component, Job→Type, CreatedBy→Contact), format (email, ISO 8601, numeric ranges, category regex), AIR (required attributes per asset class).
5. Validation report: HTML per-sheet summary + issue table, CSV, JSON. Each issue: sheet, row, column, rule id, severity (blocking/warning), message, suggested fix. Handover readiness score (weighted completeness). Exit code ≠ 0 on blocking errors.
6. Handover loader: map COBie Type/Component/Space to staging tables → match to existing assets (serial, IFC GlobalId, space+type) → inserted/updated/unchanged/rejected counts; rejects to quarantine; load audit table; idempotent re-run; `--dry-run` diff report. Map COBie category to internal `asset_type`.
7. Tests: each rule type (pass + fail fixtures); valid workbook zero blocking; loader idempotent; AIR change alters results without code change.
8. Acceptance: every seeded error found with correct rule id (confusion matrix in README); valid workbook zero blocking; idempotent loader; unit tests per rule type; AIR editable YAML.

## Risks
- COBie spec details must be verified, not invented — fetch buildingSMART + UK BIM Framework pages, record URLs in `docs/SOURCES.md`.
- Multi-value Component→Space cells need parsing; verify expected format from spec.
- Loader matching to `data/truth/assets.parquet` needs a stable key mapping; verify against P01/P04 truth model.

## Open questions
- Exact COBie sheet/column order — verify from spec PDF/HTML before coding rules.
