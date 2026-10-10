# ACCEPTANCE P20 — Governance and data-literacy pack (2026-10-09)

> Synthetic data throughout. Nothing in this pack describes a real university estate, and nothing in it is a compliance statement.

## What was delivered

| Item | Where |
|---|---|
| Governance framework, roles, decision rights, escalation | `projects/p20-governance-literacy/docs/governance/` |
| RACI for five domains, generated from `raci.yml` | `projects/p20-governance-literacy/docs/generated/raci.md` |
| Data dictionary guide + generated dictionary and lineage | `docs/data/dictionary.md`, `docs/generated/data-dictionary.md`, `docs/generated/lineage.md` |
| Business glossary (68 terms) with owner, source, refresh, DQ score, classification | `docs/generated/glossary.md` |
| Metric registry (74 entries) | `projects/p20-governance-literacy/metrics.yml`, `docs/generated/metric-registry.md` |
| Data classification and UK GDPR awareness note | `docs/data/classification.md` |
| Data quality policy page | `docs/data/quality-policy.md` |
| Naming and modelling standards | `docs/data/naming-standards.md` |
| Standards register with honest statuses | `standards.yml`, `docs/generated/standards-register.md`, `docs/standards/index.md` |
| Information handover guide (AIR checklist) | `docs/standards/handover.md` |
| Data request and change process, metric change log | `docs/process/` |
| "How to read our dashboards", one page per dashboard plus the DQ scorecard | `docs/dashboards/` |
| Training kit: 10-minute demo, 45-minute workshop, 3 exercises, quiz, answer key, feedback form, slide outline, facilitator notes | `docs/training/` |
| Runbooks and ADR index | `docs/runbooks.md`, `docs/adr-index.md` |
| Generators, link checker, readability scorer, seven gates, CLI | `src/` |
| Tests, fixtures | `tests/` (123 tests) |

## Acceptance criteria, one by one

### 1. `mkdocs build --strict` passes; link checker clean

| Check | Result |
|---|---|
| `python -m mkdocs build --strict -f projects/p20-governance-literacy/mkdocs.yml` | passes, 37 HTML pages, 0 warnings, 2.7s |
| `python projects/p20-governance-literacy/src/cli.py links` | 107 in-site links resolved, 0 broken, 0 anchors unresolved |
| Link checker unit tests | 9 tests: clean tree, missing file, missing anchor, link outside `docs_dir`, external link counted, fenced code ignored, image link checked |

External URLs (standards sources) are written as plain text, not Markdown links, so the build stays offline and nothing pretends to have been verified. The checker counts external links and reports them rather than fetching them; with zero Markdown external links in the site the count is 0.

### 2. Glossary and metric registry cover 100% of dashboard KPIs (test)

| Measure | Value |
|---|---|
| Dashboard KPI names found by scanning | **69** (P06 12, P07 24, P08 9, P09 9, P10 7, P11 9) |
| Registry entries | **74** (69 live on a dashboard, 5 marked planned) |
| Registry coverage of dashboard KPIs | **69/69**, no unmatched KPI |
| Registry entries with no dashboard consumer | **0** live (5 planned entries are excluded by the rule and must state why) |
| Glossary aliases | **69**, exactly the KPI set |
| Glossary terms | **68**, every one with owner, source of truth, refresh, classification and a DQ score or an honest "not measured" |

Both directions are enforced by tests: `tests/test_registry.py::test_real_registry_covers_every_dashboard_kpi` and `tests/test_glossary.py::test_glossary_covers_every_dashboard_kpi`. Removing one alias fails the suite (demonstrated in `tests/test_cli.py::test_undefined_kpi_fails_the_coverage_gate`).

KPI discovery rule, documented in `src/dashboards.py`: a measure is a definition at column 0 containing `=`, or a comment definition (`--`/`//`), with DAX keywords (`VAR`, `RETURN`, `SWITCH`, ...) skipped; the same rules apply inside a fenced `dax` block in `powerbi/model.md` (P10 declares its seven measures there); plus every public function in a dashboard `src/kpis.py`. Tested against hand-written DAX and `model.md` fixtures. P07 publishes two identifiers for the same underlying measure (a Power BI measure and a Python helper); both are registered and the caveat says so. `Total Energy kWh` is published by P08 and P10: one registry entry listing both consumers, so the two reports cannot drift apart.

Scan scope is explicit: P06 to P11 are scanned, P16 is excluded with the reason "mid-build, registry entries land with its handover", and `test_scan_scope_covers_every_handoff` fails if a project ships a hand-off file without either being scanned or excluded.

### 3. Literacy readability measured, target Flesch ≥ 50, numbers reported

Measured with `textstat==0.7.3` (pinned: later versions need an NLTK corpus download at runtime, which breaks offline CI). Tables, code blocks and link targets are stripped before scoring.

| Page | Flesch | Words |
|---|---|---|
| dashboards/index.md | 85.7 | 254 |
| dashboards/p06-space-utilisation.md | 76.2 | 337 |
| dashboards/p07-assets-and-maintenance.md | 76.8 | 284 |
| dashboards/p08-energy-and-carbon.md | 69.4 | 323 |
| dashboards/p09-compliance.md | 77.6 | 330 |
| dashboards/p10-institutional-return.md | 76.9 | 260 |
| dashboards/data-quality-scorecard.md | 76.0 | 402 |
| training/ten-minute-demo.md | 87.5 | 514 |
| training/workshop.md | 75.9 | 369 |
| training/exercises.md | 76.4 | 603 |
| training/quiz.md | 77.7 | 262 |
| training/answer-key.md | 76.0 | 61 |
| training/feedback-form.md | 67.3 | 62 |
| training/slide-outline.md | 69.6 | 37 |
| training/facilitator-notes.md | 85.0 | 456 |

**Min 67.4, mean 76.9, 15 of 15 pages above the target of 50.** The lowest is the feedback form (67.3), which is short and mostly tick-boxes; the highest is the demo script (87.5), which is written as spoken sentences. No page was rewritten to game the number, and the generated technical pages are excluded on purpose.

### 4. Workshop pack complete enough to deliver from the folder alone

| Element | Present |
|---|---|
| 10-minute demo script with timings and what to do if asked something unanswerable | yes |
| 45-minute workshop: outcomes, timed plan, materials checklist, adaptations (half-day, technical, senior, online) | yes |
| Three exercises with briefs, tasks and answers in the same folder | yes (plus an optional fourth) |
| Quiz: 12 questions (10 core, 2 challenge) | yes |
| Answer key with what to look for, scoring bands, and a "not for performance" note | yes |
| Feedback form with instructions for using the answers | yes |
| Slide outline only, explicitly left for the human to build | yes |
| Facilitator notes: setup, the three questions always asked, the two quiet moments, what not to do, follow-up | yes |

Tested by `tests/test_content.py::test_workshop_pack_is_deliverable_from_the_folder_alone` and the quiz/key pairing test.

## Gates (all run by `python projects/p20-governance-literacy/src/cli.py check`)

```
PASS metric registry schema - 68 entries, 7 owners
PASS glossary schema - 66 terms, 19 required by the spec
PASS KPI scan scope - scanned ['p06','p07','p08','p09','p10','p11'], excluded ['p16']
PASS dashboard KPI coverage (registry + glossary) - 63 dashboard KPI names checked both ways
PASS generated pages not stale - 7 generated pages compared
PASS in-site links - 107 in-site links resolved, 0 external links not fetched
PASS literacy page readability - 15/15 measured, min 67.35, mean 76.9, target 50.0
```

## Local verification (Windows, Python 3.13, seed 42 synthetic data)

| Check | Command | Result |
|---|---|---|
| Tests | `python -m pytest projects/p20-governance-literacy/tests -q --no-cov` | **127 passed**, 25s |
| Coverage of P20 modules | same with `--cov=projects/p20-governance-literacy/src` | **96%** (`checks.py` 99%, `cli.py` 88%, `dashboards.py` 97%, `dbt_meta.py` 96%, `generate.py` 99%, `glossary.py` 94%, `links.py` 99%, `metrics.py` 92%, `readability.py` 100%) |
| Lint and format | `ruff check projects/p20-governance-literacy` / `ruff format --check` | clean |
| Regenerate pages | `python projects/p20-governance-literacy/src/cli.py build` | 7 pages, idempotent (second run: 0 updated) |
| Site build | `mkdocs build --strict -f projects/p20-governance-literacy/mkdocs.yml` | passes |
| Everything | `make p20-run` | build + test + check + strict site build |

## Generated content, from real artefacts in this checkout

| Page | What it found |
|---|---|
| dictionary | 45 models, 5 layers (staging, intermediate, marts, seeds, snapshots), every column with type, description and tests |
| lineage | 55 edges from `{{ ref() }}` and `{{ source() }}` plus `exposures.yml`; 5 dashboard exposures with their dependencies |
| DQ scores | run `r7`: assets 99.7, bms 100.0, inspections 99.4, meters_a 85.8, meters_b 82.9, sensors 93.2, spaces 99.9, timetable 93.0, work_orders 95.3, plus per-dimension scores, failing checks and alerts |
| glossary | 68 terms with the DQ score of each term's dataset joined from that run |
| registry | 74 entries with formula, grain, owner, version, caveats, classification and glossary cross-reference |
| standards | 10 standards: 4 implemented, 2 mock, 3 awareness-only, 1 not-obtained |
| RACI | 4 roles, 5 domains, 23 activities, each with exactly one accountable role |

## Deviations from the spec, stated plainly

1. **Dictionary and lineage are built from the dbt YAML and SQL, not from `manifest.json`.** The spec says scripts generate pages from `manifest.json`/`catalog.json`. No manifest is committed in this repository (it is a build artefact under `platform/dbt/target/`, which is git ignored), so the generator reads the reviewed YAML and the model SQL instead. `dbt_meta.load()` prefers a real `manifest.json` when one exists, and that path is implemented and tested (`tests/test_generators.py::test_manifest_path_is_preferred`).
2. **P10 has no Power BI hand-off and no source in this checkout**, so it contributes no KPI names to the scan. Its dashboard page describes the return pack from the outputs that are present in `data/p10_output/` and says plainly that the project's code is missing. Recorded in `STATUS.md`.
3. **P16 is excluded from the KPI scan** (mid-build, uncommitted). The exclusion is in `src/config.py` with a reason, and a test fails if a hand-off file appears unswept.
4. **The site is built separately from the portfolio site** (`projects/p20-governance-literacy/mkdocs.yml`), and `docs.yml` copies it into the published site under `governance-pack/`. The root `Makefile` `docs` target builds both. This keeps the P20 nav and gates independent while still publishing it.
5. **Cross-project references are code spans, not links.** `mkdocs build --strict` fails on links outside a site's `docs_dir`, and `docs/reference-index.md` lists every repository path as text instead.
6. **External links are not fetched.** CI must not depend on the network. Standards URLs are plain text, so the count of external Markdown links in the site is 0 and nothing is claimed as verified.
7. **textstat is pinned to 0.7.3.** 0.7.13 requires an NLTK `cmudict` download at first use; the proxy in this environment refuses it, and a documentation gate that needs a network fetch would be a bad gate. The reason is in `pyproject.toml`.
8. **Repository-wide `ruff check .` is not clean: 155 findings in other projects** (`p17`, `p18`, `p10`, `p09`, `demos`, `orchestration`) that are mid-build or uncommitted by other work. P20 itself is clean. Not fixed here: it would mean editing projects outside this task.

## Open for a human

- Ratify the roles, owners and service levels with named people and a data protection contact.
- Replace the illustrative compliance frequencies with values from the legal source, recorded with version and URL.
- Obtain the HESA EMR specification and the licensed Uniclass tables, then move those standards from `mock`/`awareness-only` to `implemented`.
- Add a nightly job with network access to check external links.
- Run the workshop with a real cohort and record the measured change in confidence in `README.md` §5.
- Enable GitHub Pages (the site is already copied into the published portfolio site by `docs.yml`).