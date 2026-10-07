# P14 — ISO 19650-style compliance checker

**Location:** `projects/p14-iso19650-checker/`
**Criteria:** E6, E7, D6
**Stack:** Python, Typer, Pydantic v2, PyYAML, Jinja2, pytest; optional ifcopenshell / python-docx / pypdf / openpyxl for metadata.
**Goal:** a convention-agnostic checker that validates file/container naming and metadata against a
configurable information-management convention.

> **Verify the convention first.** The spec's author recalled a typical UK-style field pattern
> *(Project – Originator – Volume/System – Level/Location – Type – Role – Number, with status/suitability
> and revision)* but had not verified code lists or lengths. Read the UK BIM Framework / BS EN ISO 19650
> UK National Annex guidance, record sources in `docs/SOURCES.md`, and encode what you find in
> `conventions/uk_national_annex.yml`. The engine must read **everything** from config so an
> organisation's own convention can be dropped in; ship a second, different convention in tests to prove it.

*This file is the spec section copied verbatim for traceability. Read-only: it is not a status document.
See `README.md` for how the work was done and `docs/ACCEPTANCE_P14.md` for the evidence.*

### Checks

Field count, order, length, charset and separators; values against allowed code lists; sequence number
format; revision format and sequencing gaps; status/suitability code vs container state (WIP / Shared /
Published / Archive folder); duplicate identifiers; case and illegal characters; path length; disallowed
file types; metadata consistency (filename vs document title or IFC project name where available); orphan
files missing from the container register.

### Features

- `iso19650-check <folder> --config conventions/uk_example.yml --format html|json|junit`
- `--suggest` mode lists fixes for trivially fixable issues (case, separators) and never renames;
  `--apply` renames with a dry-run default and a rollback log.
- Generates `container_register.csv` and a compliance summary (compliance % by field, by folder, by
  originator).
- Sample project folder generator (~300 files, seeded issues of every category, logged to a truth file).
- Pre-commit hook and GitHub Action examples; JUnit output for CI.

### Acceptance

- Every seeded issue category detected; false positives = 0 on the clean sample.
- Swapping convention file changes behaviour with no code edits (test with two conventions).
- `--apply` is reversible (rollback test).
- README lists what is configurable and what is *not* checked (honest scope).

---

### How the implementation maps to the spec (deviations recorded here for the next reader)

| Spec item | Implementation | Note |
|---|---|---|
| `--format html\|json\|junit` | plus `text` (default) | Text is the terminal summary; the other three write files to `--out`. |
| `--config conventions/uk_example.yml` | `conventions/uk_national_annex.yml` | `uk_example.yml` was removed: its fixed 6-character widths, `VO`/`LL`/`TY`/`RO` field names and `WIP` status code were not supported by the source. Renamed rather than quietly patched. |
| field count is a check | `field_count` fires only when there are **more** fields than declared | The Annex says the number of fields "can be shortened or expanded as required"; a missing declared field is still an error (`field_missing`). |
| duplicate identifiers | Scoped to (container state, id, revision) | The same id in two states is the container lifecycle; the same id with different revisions is a revision history, reported by `revision_gap` instead. |
| status/suitability code list | `pattern` instead of a closed list | The `A`/`B` series is open-ended ("n" = project stage), so a list would be wrong. |
| sequence number format | `field_charset` + length + `number_gap` warning | "Format" for a sequential number is digits plus width; gaps are warnings, since a missing container may simply not have been produced yet. |
| metadata consistency | `.ifc`, `.docx`, `.pdf`, `.xlsx`, `.txt`/`.md` | Optional dependencies, imported lazily; a missing backend is reported as *skipped*, never as a pass. |
| orphan files | `--register <csv>` compares on-disk files with a supplied register | Without a register there is nothing to compare against, so the rule is inert rather than guessing. |
| pre-commit hook / GitHub Action | `examples/` directory | Examples, not wired into this repo's CI: the sample project is generated, not committed. |
