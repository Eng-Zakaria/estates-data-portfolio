# PLAN: P14 ISO 19650-style convention checker

Status: resumed 2026-10-06 (code existed but SPEC/docs/acceptance missing; several spec features
were still unimplemented: revision/sequence checks, `--suggest`/`--apply`/rollback, compliance
summary, metadata consistency, orphan files, CI examples, second convention).

## Goal
A convention-agnostic checker that validates file/container naming and metadata against a configurable
information-management convention. The engine reads everything from config, so an organisation's own
convention can be dropped in; a second, different convention ships in `conventions/` to prove it.

## Research (done 2026-10-06 — see projects/p14-iso19650-checker/docs/SOURCES.md)

Convention details are **not** taken from memory. Fetched and read:

- **CDBB "BIM Toolkit | National Annex Guidance"** (UK instantiation of the ISO 19650 principles):
  7 identification fields, hyphen-minus (U+002D) delimiter, per-field character counts, level/location,
  type and discipline code lists, status code table, revision (P/C + two integers, WIP `.nn` suffix).
- **UK BIM Framework, Guidance Part C, Edition 1 (Sept 2020)**: CDE states (WIP/Shared/Published/Archive),
  status codes in use, worked example S0 `P01.01` → S3 `P01` → S4 → A3 `C01`, and the status→state
  statement ("…with S1 or S2 metadata are in the Shared state, whereas … A4, A5 or A6 … Published").

Consequences for the code:

- Fields 1–7 keep their Annex names/orders/lengths. The old `uk_example.yml` (6-char fixed lengths,
  `VO`/`LL`/`TY`/`RO` field names, `WIP` as a status code, `S6`/`S7` in use) was **not** supported by the
  source and has been replaced by `conventions/uk_national_annex.yml`. Removed, not silently "fixed".
- Status codes are 2 characters (`S0`–`S6`, `A1…An`, `B1…Bn`, `CR`); the `A`/`B` series is open-ended
  (stage-driven), so the status field is validated by **pattern**, not a closed code list.
- Revisions are `P`/`C` + two integers, with a `.nn` version suffix for WIP containers.
- The status→container-state map is an **example instantiation** (the guidance requires the appointing
  party to record it in the project information standard); it is labelled as such in the config.

## Tasks

1. [x] Source research; record in `docs/SOURCES.md`; encode in `conventions/uk_national_annex.yml`.
2. [x] Scaffold `src/`, `tests/`, `docs/`, `conventions/`, examples.
3. [x] Convention config schema (Pydantic): per-field name/position/min+max length/charset/pattern/
   allowed values/required/source note; convention-level separator, case policy, illegal characters,
   extension allowlist, path limits, container states, sequence + revision rules, metadata rules.
4. [x] Checker engine: field count/order/length/charset/pattern/values; illegal characters; case;
   extension; path length; status vs container state; duplicate identifiers; number-sequence gaps;
   revision format + gaps; metadata consistency (optional ifcopenshell/docx/pypdf/openpyxl); orphan
   files vs a supplied container register.
5. [x] CLI: `check --format text|html|json|junit`, `--suggest`, `--fail-on`, `--register`;
   `apply` (dry-run by default, `rename_log.csv`), `rollback`. Writes `container_register.csv`
   (with sha256) and `compliance_summary.csv` (by field, by folder, by originator).
6. [x] Sample generator: 300 files, clean mode, seeded issues of every category + truth file.
7. [x] Second convention (`conventions/estates_cde_variant.yml`) + pre-commit hook and GitHub Action examples.
8. [x] Tests: seeded-category recall, zero false positives on the clean sample, config swap changes
   behaviour with no code edit, `--apply` reversible, hand-checked fixtures for sequencing/revision.
9. [x] Acceptance evidence in `docs/ACCEPTANCE_P14.md`; SPEC.md copy; README per template; DATA.md
   provenance; STATUS.md row.

## Risks / decisions

- **Metadata checks stay optional.** `metadata.py` imports ifcopenshell/python-docx/pypdf/openpyxl
  lazily; the naming checks run with none of them installed. If a backend is missing the check is
  skipped and reported as skipped, never silently "passed".
- **False positives are the acceptance gate**, so trivially-fixable rules (case, separator) are
  warnings with a suggested rename, and `--apply` only renames when every error on a file is fixable.
- The second convention is an *organisation-specific instantiation* of the same verified Annex
  (expanded schedules are explicitly permitted: Annex §1.2.3–1.2.6), not an invented national standard.
- Gap/sequence rules are warnings, not errors: a missing `0003` may legitimately mean "not produced yet".
