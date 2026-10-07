# P14 acceptance evidence

**Date:** 2026-10-07 · **Convention:** `uk_national_annex` (CDBB BIM Toolkit / National Annex guidance,
read 2026-10-06) · **Sample:** `data/iso19650/sample`, 301 files, seed 42 · **All data synthetic.**

Reproduce from a clean clone:

```bash
make p14-run          # sample + tests + seeded check + clean check + second convention
```

Individual commands and their measured output are quoted below. Numbers are pasted exactly as measured.

---

## 1. Acceptance criteria from the spec

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Every seeded issue category detected | **PASS** — 20/20 rule ids fire; every planted rule reported against its own file | §2, §3 · `tests/test_sample.py` |
| 2 | False positives = 0 on the clean sample | **PASS** — 200 files, 0 errors, 0 warnings; and 120/120 for the second convention | §4 · `tests/test_sample.py` |
| 3 | Swapping the convention file changes behaviour with no code edits | **PASS** — same 120 files: 0 findings vs 1320 errors | §5 · `tests/test_conventions.py` |
| 4 | `--apply` is reversible (rollback test) | **PASS** — applied 2 renames, rolled back 2, tree byte-identical by sha256 | §6 · `tests/test_rename.py` |
| 5 | README lists what is configurable and what is *not* checked | **PASS** — README §8 | — |

## 2. Every seeded category detected

Generator: `python projects/p14-iso19650-checker/src/make_sample.py --out data/iso19650/sample --n 300 --seed 42`

```
Generated 301 files in data\iso19650\sample (seed 42): 18 seeded issue files, 1 orphan(s).
```

Checker: `python projects/p14-iso19650-checker/src/cli.py check data/iso19650/sample --config projects/p14-iso19650-checker/conventions/uk_national_annex.yml --register data/iso19650/sample_register.csv --suggest --out data/iso19650/report`

```
Convention: uk_national_annex
Root:       data\iso19650\sample
Files:      301
Compliance: 94.0% compliant (75 errors, 9 warnings in 18 files)

Findings by rule:
  disallowed_extension           1  error      status_container_mismatch     6  error
  duplicate_identifier           1  error      stem_length                   1  warning
  empty_field                    1  error      field_allowed_values         12  error
  field_case                     5  warning    field_charset                12  error
  field_count                    4  error      field_length                 14  error
  field_missing                  9  error      field_pattern                 7  error
  illegal_character              1  error      metadata_mismatch             2  error
  number_gap                     1  warning    orphan_file                   1  error
  path_length                    1  warning    revision_format               3  error
  revision_gap                   1  warning    separator_misuse              1  error
```

Exit code **1** (errors present) — the CI gate fires.

`test_every_seeded_category_is_detected` checks this per file rather than per rule: for each of the 18
planted files, every rule it was planted with is reported against *that file*. `missed == []`.

## 3. Seed → detection map

| Planted rule | File (relative to the sample root) | Detected |
|---|---|---|
| `field_count` | `WIP/Seeds/SD01-…-S0-EXTRA.docx` | yes |
| `field_missing` | `WIP/Seeds/SD02-…-0001-P01.01.docx` | yes |
| `field_length` (short) | `WIP/Seeds/P-QSUR-…-S0-P01.01.txt` | yes |
| `field_length` (long) | `WIP/Seeds/SD04-ORIGINATOR-ONE-…txt` | yes |
| `field_charset` | `WIP/Seeds/SD05-ENGG-ZZ-ZZ-AF-9-0001-S0-P01.01.txt` | yes |
| `field_allowed_values` | `WIP/Seeds/SD06-FMVS-ZZ-99-AF-A-0001-S0-P01.01.docx` | yes |
| `field_pattern` (status) | `WIP/Seeds/SD07-ARCV-ZZ-ZZ-AF-A-0001-S9-P01.01.txt` | yes |
| `revision_format` | `WIP/Seeds/SD08-QSUR-ZZ-ZZ-AF-A-0001-S0-X1.txt` | yes |
| `field_case` | `WIP/Seeds/SD09-struct-zz-…-S0-P01.01.txt` | yes (warning) |
| `illegal_character` | `WIP/Seeds/SD10-ES@M-ZZ-ZZ-AF-A-0001-S0-P01.01.txt` | yes |
| `separator_misuse` | `WIP/Seeds/SD11_ENGG_ZZ_ZZ_AF_A_0001_S0_P01.01.txt` | yes |
| `empty_field` | `WIP/Seeds/SD12--ARCV-ZZ-ZZ-AF-A-0001-S0-P01.01.txt` | yes |
| `disallowed_extension` | `WIP/Seeds/SD13-FMVS-…-0001-S0-P01.01.exe` | yes |
| `status_container_mismatch` | `WIP/Seeds/SD14-ESTM-ZZ-ZZ-AF-A-0001-CR-P01.01.txt` | yes |
| `metadata_mismatch` | `WIP/Seeds/SD15-ARCV-…-S0-P01.01.txt` (title "Site walkaround notes") | yes |
| `duplicate_identifier` | `WIP/Seeds/ZCopy/SD91-…-S0-P01.01.txt` | yes |
| `orphan_file` | `WIP/Seeds/SD92-…-S0-P01.01.docx` (absent from the register) | yes |
| `path_length` + `stem_length` | `WIP/Archive/VeryLongFolderName…/SD90-…-PADDING×12.txt` | yes |
| `number_gap` (series) | `GAP01` series 0001, 0002, **0004** | yes — `number 0003 is missing` |
| `revision_gap` (series) | `REV01` series P01, **P03** | yes — `P revision … 02 is missing` |

## 4. False positives = 0 on a clean sample

```
$ python projects/p14-iso19650-checker/src/make_sample.py --out data/iso19650/clean --n 200 --clean
Generated 200 files in data\iso19650\clean (seed 42): 0 seeded issue files, 0 orphan(s).

$ python projects/p14-iso19650-checker/src/cli.py check data/iso19650/clean --config …/uk_national_annex.yml --register data/iso19650/clean_register.csv
Convention: uk_national_annex
Root:       data\iso19650\clean
Files:      200
Compliance: 100.0% compliant (0 errors, 0 warnings in 0 files)

Findings by rule:
  (none)
```

Exit code **0**. Also asserted per test: `result.issues == []` and `compliance_pct() == 100.0`
(`test_false_positives_are_zero_on_the_clean_sample`), and identically for the second convention's
120-container clean sample (`test_false_positives_are_zero_for_the_second_convention`).

Two false-positive traps found and fixed while building this, both now regression-tested:

- **Cross-state identifiers.** Scoping duplicate detection globally flagged 140 false duplicates, because
  one container legitimately appears in WIP, Published and Archive over its life. Now scoped to
  (state, id, revision) — `test_duplicate_identifier_is_scoped_to_state_and_revision`.
- **Cross-folder series.** Number-gap detection keyed on the identifier alone reported 78 false gaps,
  because one series was split across sibling folders. Now keyed on (folder, identifier) —
  `test_number_gap_is_scoped_to_the_folder`.

## 5. Swapping the convention changes behaviour

Same 120 files, same command, only `--config` differs:

```
$ python …/cli.py check data/iso19650/variant --config …/conventions/estates_cde_variant.yml
Files: 120 → Compliance: 100.0% (0 errors, 0 warnings)          exit 0

$ python …/cli.py check data/iso19650/variant --config …/conventions/uk_national_annex.yml
Files: 120 → Compliance: 0.0% (1320 errors, 0 warnings)         exit 1
   separator_misuse 120 · field_length 120 · field_charset 120 · field_missing 960
```

Every one of those is explained by the convention differing: `estates_cde_variant` uses `_` as separator,
5-character project codes, a 10th `asset_class` facet, an extra `PR1` facet, 3–4 digit numbers and word
statuses (`WIP`/`REV`/`INFO`/`APPROVED`/`SUPERSEDED`). `test_one_name_judged_by_two_conventions` pins
the same behaviour on a single hand-written file, and `test_variant_convention_is_a_different_shape`
fails if the two conventions ever stop differing.

## 6. `--apply` is reversible

```
$ python …/cli.py apply data/iso19650/sample --log data/iso19650/report/rename_log.csv
DRY RUN - nothing renamed: 2 rename(s), 0 skipped.

$ python …/cli.py apply data/iso19650/sample --log …/rename_log.csv --apply
APPLIED: 2 rename(s), 0 skipped.
Rollback with: iso19650-rollback data/iso19650/sample --log …/rename_log.csv

$ python …/cli.py rollback data/iso19650/sample --log …/rename_log.csv
Rolled back 2 rename(s), 0 skipped (log: …/rename_log.csv).
```

The two renames: `SD09-struct-zz-…` → `SD09-STRUCT-ZZ-…` (case) and `SD11_ENGG_…` → `SD11-ENGG-…`
(separator). `rename_log.csv` records timestamp, both paths, status and the pre-rename sha256;
rollback re-hashes before restoring.

Automated equivalents: `test_apply_then_rollback_restores_the_tree_exactly` (full byte-for-byte tree
comparison), `test_rollback_handles_case_only_renames` (Windows case-insensitive filesystem), and the
refusals — edited content, occupied target, missing source, dry-run rows.

## 7. Tests, coverage, lint

```
$ make p14-test
83 passed in 65.67s (0:01:05)

Name                          Stmts   Miss  Cover   Missing
projects\p14-…\src\checker.py     486     13    97%   111-115, 195, 211, 236, 267, 394, 405, 749, 784
projects\p14-…\src\cli.py           69      6    91%   21, 63, 122, 149, 151, 155
projects\p14-…\src\make_sample.py  405     28    93%   …
projects\p14-…\src\metadata.py     141     13    91%   …
projects\p14-…\src\rename.py        96      8    92%   …
projects\p14-…\src\reporting.py     60      3    95%   …
TOTAL                            1257     71    94%

$ ruff check projects/p14-iso19650-checker/     → All checks passed!
$ ruff format --check projects/p14-iso19650-checker/ → 13 files already formatted
```

Core-module coverage ≥ 91% (requirement ≥ 80%). The uncovered lines are `if __name__ == "__main__"`
guards, an OSError branch in `rename.py` and the pydantic `model_copy` path.

`mypy --strict` is **not** run over P14: the repo's `make typecheck` scope is `packages/campus_synth`
and `platform/` (AGENTS.md: "strict on shared packages"). The P14 modules are fully annotated anyway.

## 8. Reproducibility and determinism

- Seeded generator: same seed → byte-identical tree and truth file
  (`test_generator_is_deterministic`); seed 42 vs 43 produce different trees.
- `test_same_folder_same_convention_is_deterministic` pins report stability.
- Reports are written to `data/iso19650/` (gitignored); `make p14-sample` regenerates in ~13 s.
- Check runtime 7.1 s for 301 files, including a sha256 per container for the register.

## 9. Convention provenance (AGENTS.md rule 4)

`conventions/uk_national_annex.yml` is not written from memory. Every value traces to a source read on
2026-10-06 and quoted in [`SOURCES.md`](SOURCES.md):

- CDBB, *BIM Toolkit | National Annex Guidance*, https://www.cdbb.cam.ac.uk/files/national_annex_guidance.pdf
  — fields and order, hyphen-minus (U+002D) delimiter, character counts per field, level/location
  (Table 1.3), type (Table 1.4), discipline (Table 1.5), status codes (Table 2.2), revision format (§2.1.1).
- UK BIM Framework, *Guidance Part C, Edition 1, September 2020* — CDE container states, statuses in use
  (S6 added, S7 withdrawn), status-to-state statement, worked progression S0/P01.01 → S3/P01 → S4 →
  A3/C01.

Values deliberately **not** from those sources (extension allowlist, illegal characters, path/stem
limits, case policy, `metadata.required_title_fields`) are listed as local policy in `SOURCES.md` §3.

The first-pass `conventions/uk_example.yml` was **removed**, not patched: its fixed 6-character widths,
`VO`/`LL`/`TY`/`RO` field names and `WIP` status code were not supported by any source read.

## 10. Known limitations (see README §8 for the full list)

- Metadata checks read document titles / IFC header project names only; content is not validated.
- Level and type code lists are *seeded* from the published Annex tables. The Annex allows projects to
  extend them, so a real project must review these lists before using the checker as a gate.
- The status-to-state map is an example instantiation derived from the Part C worked progression.
- No CDE integration: status/revision are inferred from the file name only; a CDE export manifest would
  be the next input to support.
- The `2021` update to the UK National Annex (reported by secondary sources, not obtained) may rename
  fields; that edition is not encoded. Logged in `SOURCES.md` §5 and `docs/OPEN_QUESTIONS.md`.
