# PLAN: P20 Governance and data-literacy pack

## Goal

A publishable governance + literacy site (MkDocs Material) that other people can
actually use: who owns which data, what each metric means, how data is
classified, what our standards are (with honest status), how a project hands
information over to operations, how to ask for data, how to read each dashboard,
and a 45-minute workshop pack somebody else could deliver from the folder alone.

Two things make it more than a wiki: the **metric registry is tested** against
the KPI names that actually appear in the Power BI handoff files (`measures.dax`)
and the KPI helper modules (`p07/src/kpis.py`), and the **dictionary, lineage,
DQ-score, glossary, RACI, standards and registry pages are generated** from
artefacts so they cannot drift silently (CI fails when they do).

## Why P20 now

Last project in the build order. Everything it documents exists: P01-P05 give
the lakehouse, dbt marts, DQ policy and CI; P06-P11 give the dashboards and
`measures.dax` files that the registry must cover; P12/P14 give the COBie and
ISO 19650 checks the handover guide links to.

## Key decisions (spec-driven)

- **Own MkDocs site**, not a tab of the root site: `projects/p20-governance-literacy/mkdocs.yml`
  with `docs_dir: docs`. Root `mkdocs.yml` keeps the portfolio docs; P20 gets its
  own build so `mkdocs build --strict` runs on its own nav, and a link in the root
  site/README points at it.
- **Machine-readable source, generated pages.** `metrics.yml`, `glossary.yml`,
  `raci.yml`, `standards.yml` in the project root are the source of truth;
  `docs/generated/*.md` are rendered by `src/generate.py`. Hand-written prose
  lives in `docs/**` and never duplicates a generated table.
- **Cross-project links are code spans, not links.** Other projects' docs are
  outside this site's `docs_dir`, and `mkdocs build --strict` warns (fails) on
  such links. So `docs/reference-index.md` lists repo-relative paths as text. The
  link checker therefore only validates in-site links (and reports how many
  external/code-span references it skipped) — no silent external-link checking.
- **Metric registry coverage rule** (tested both ways):
  - *in → registry*: every measure name in `projects/p06..p11/**/measures.dax`
    and every public function in a dashboard `src/kpis.py` has exactly one entry
    in `metrics.yml`, keyed by the dashboard KPI name;
  - *registry → consumers*: every entry names at least one consumer
    (`dashboards:` project ids, all of which must exist) or is marked
    `status: planned` with a note. Helpers (`kind: helper`, e.g. `mttr`
    arguments, band functions) are registered too — they are things people
    misread, so they get a definition.
- **Glossary coverage rule** (acceptance "glossary and metric registry cover
  100% of dashboard KPIs"): `glossary.yml` has a `kpi_aliases` map from every
  dashboard KPI name to a glossary term. Test asserts the two sets are equal and
  every alias target exists. Plus a required-terms list from the spec
  (GIA, NIA, FTE, PPM, reactive, MTTR, utilisation, Scope 1, Scope 2, baseload,
  COBie, AIR, ...).
- **Dictionary/lineage from dbt without a manifest.** `manifest.json` is not
  committed (it is a build artefact), so `src/dbt_meta.py` parses
  `platform/dbt/models/*.yml` (descriptions, types, tests) and the SQL for
  `{{ ref() }}`/`{{ source() }}` edges, plus `exposures.yml`. If a real
  `manifest.json`/`catalog.json` ever gets committed, `dbt_meta` reads it first
  (documented in code) — one code path, two sources.
- **DQ score page degrades gracefully.** `data/quality/gold/dq_scores.csv` →
  else DuckDB `mart_dq_scorecard` → else a page that says "no results yet" and
  lists the command to produce them. Never fails the build for missing data.
- **Readability gate on the literacy pages only.** `textstat.flesch_reading_ease`
  on prose (tables/code stripped) for `docs/dashboards/*.md` and
  `docs/training/*.md`; target >= 50, numbers printed and reported in the README
  and acceptance doc whether they pass or not.
- **Standards register status is honest**: `implemented` / `mock` /
  `awareness-only` / `not-obtained`, with the provenance URL and the project
  that encodes it. Uniclass (P13) is a dev placeholder, so its status is
  `mock`, and the entry says so. No code lists are reproduced.
- **UK GDPR note is awareness only**, explicitly not legal advice, with the
  realistic estates cases (names on work orders, sensor headcounts) and the
  handling rule actually implemented in this repo.

## Tasks

1. `docs/PLAN_P20.md` (this file).
2. `SPEC.md` (copy of the P20 section) + data files `metrics.yml`, `glossary.yml`,
   `raci.yml`, `standards.yml`.
3. `src/`: `config.py`, `metrics.py`, `glossary.py`, `dbt_meta.py`,
   `generate.py`, `links.py`, `readability.py`, `checks.py`, `cli.py`.
4. `docs/`: index, governance (framework/roles/generated RACI), data
   (dictionary/glossary/registry/classification/dq-policy/naming), standards
   (register/handover), process (data request + metric change log), dashboards
   (index + 5 dashboard pages + DQ scorecard), training (demo, workshop, quiz,
   answer key, feedback form, slide outline, facilitator notes), runbooks,
   ADR index, reference index, `generated/` (7 pages).
5. `tests/`: registry schema + coverage, glossary coverage, generators on
   fixtures, determinism/staleness, link checker (fixture + site), readability
   (fixture + site gate), content completeness (nav, workshop pack, standards
   statuses, RACI).
6. `README.md`, `mkdocs.yml`, project `Makefile`, root `Makefile` target
   `p20-run`/`p20-build`/`p20-check`, CI step, `DATA.md`, `STATUS.md`,
   acceptance doc, commits.

## Risks

- **Strict MkDocs build fails on nav/anchor issues** → build locally before
  claiming it passes; `--strict` warnings are errors.
- **Readability below 50 on some pages** → report measured values; rewrite the
  worst offenders in short sentences rather than gaming the metric, and if a
  page stays low, say so in the acceptance doc.
- **Registry drift from dashboards** → that is the point of the test; failure
  means add the entry or fix the dashboard, never loosen the test.
- **Generated pages stale** → `make p20-check` regenerates into a temp dir and
  diffs; CI runs the same check.
- Warehouse/DQ artefacts may not exist on a fresh clone → generators degrade with
  an explicit "not run" page, and the staleness check ignores pages whose inputs
  are absent.

## Open questions

- None blocking. Real deployments would want a data-protection officer sign-off
  on the classification page and an estates-wide RACI ratification; recorded as
  `docs/OPEN_QUESTIONS.md` A-05 style entries rather than blocking the build.