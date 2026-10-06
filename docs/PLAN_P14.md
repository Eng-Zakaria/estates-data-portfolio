# PLAN: P14 ISO 19650-style compliance checker

## Goal
A convention-agnostic checker that validates file/container naming and metadata against a configurable information-management convention. Engine reads everything from config so an organisation's own convention can be dropped in; ship a second different convention in tests to prove it.

## Tasks
1. Source research: read UK BIM Framework / BS EN ISO 19650 UK National Annex guidance. Record sources in `docs/SOURCES.md`. Encode what is found in `conventions/uk_example.yml`. Do not invent code lists or lengths from memory.
2. Scaffold `projects/p14-iso19650-checker/`: `src/`, `tests/`, `docs/`, `conventions/`, `Makefile`.
3. Convention config schema (Pydantic): fields with name, position, length, charset, separator, allowed values (code list), regex pattern, required/optional, status/suitability mapping to container states.
4. Checker engine (`src/checker.py`): field count/order/length/charset/separators; values against allowed code lists; sequence format; revision format and sequencing gaps; status/suitability vs container state; duplicate identifiers; case and illegal characters; path length; disallowed file types; metadata consistency (filename vs title/IFC project name where available); orphan files missing from container register.
5. CLI (`src/cli.py`): `iso19650-check <folder> --config conventions/uk_example.yml --format html|json|junit`. `--suggest` for trivial fixes (case, separators); `--apply` renames with dry-run default and rollback log. Generates `container_register.csv` and compliance summary (% by field, folder, originator).
6. Sample project generator (`src/make_sample.py`): ~300 files, seeded issues of every category, logged to truth file.
7. Pre-commit hook and GitHub Action examples; JUnit output for CI.
8. Tests: every seeded issue category detected; false positives = 0 on clean sample; swapping convention file changes behaviour with no code edits (two conventions); `--apply` reversible (rollback test).
9. Acceptance: every seeded issue category detected; false positives = 0 on clean sample; config swap changes behaviour; `--apply` reversible; README lists configurable vs not checked.

## Risks
- Convention details must be verified from UK BIM Framework / ISO 19650 guidance, not from memory. Record URLs and versions in `docs/SOURCES.md`.
- Metadata extraction from IFC/docx/pdf requires optional dependencies; guard imports so core naming checks work without them.
- Sample generator must be deterministic (seeded) so tests are reproducible.

## Open questions
- Exact UK convention field lengths/code lists — verify from official guidance before encoding in `conventions/uk_example.yml`.
