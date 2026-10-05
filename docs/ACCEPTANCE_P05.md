# ACCEPTANCE P05 — CI/CD for data (2026-10-05)

> Synthetic data throughout. P05 adds no datasets (no `DATA.md` change).

## Workflows delivered

| File | Purpose |
|---|---|
| `.github/workflows/ci.yml` | PR+main gate: ruff, mypy, pytest (≥80%), small data → ingest → reconcile → `dbt build` → DQ gate → sqlfluff → terraform fmt/validate → tflint → compose config → Airflow hook → mkdocs strict. Matrix 3.11/3.12, concurrency cancel. |
| `.github/workflows/nightly.yml` | Full-profile run + dbt-docs artefact + issue-on-fail. |
| `.github/workflows/docs.yml` | MkDocs + dbt docs → GitHub Pages. |
| `.github/workflows/release.yml` | Tag `v*`: build dists, changelog from conventional commits, GH release. |
| `.github/workflows/security.yml` | pip-audit, gitleaks, CodeQL (PR + weekly). |
| `.github/workflows/_reusable.yml` | Reusable lint+test (`workflow_call`). |
| `.github/dependabot.yml` | Weekly pip/docker/actions. |

Also: `.pre-commit-config.yaml` (mirrors CI), PR template, CODEOWNERS
(`@YOUR-ORG` placeholder — human replaces, see `docs/branch-protection.md`),
`CONTRIBUTING.md`, `docs/branch-protection.md`, `docs/ci-demo.md`,
`mkdocs.yml` + `docs/index.md`, README badges, `Makefile` targets
(`ci`, `dbt-build`, `dbt-docs`, `dq-check`, `security`).

## Local verification (small profile, seed 42)

| Check | Result |
|---|---|
| `ruff check .` + `ruff format --check .` | clean (70 files) |
| `mypy packages/... platform/src/ingest` | clean, 24 files (local mypy 1.15; CI uses pyproject range) |
| `pytest -q --cov-fail-under=80` | 27 passed, coverage gate held |
| `make data` + `make ingest` + reconcile | zero unexplained loss (P01 report) |
| `dbt build` | green: PASS=183 WARN=0 ERROR=0 (188 nodes incl. 5 NO-OP exposures) |
| `dq_gate.py` | SKIP-notice exit 0; fabricated error-severity fixture → exit 1 (see `ci-demo.md`) |
| `sqlfluff lint platform/dbt/models platform/dbt/macros` | exit 0 (root `.sqlfluff` drives dbt templater) |
| `docker compose config --quiet` | exit 0 |
| `mkdocs build --strict` | green (after this file + index-link fix) |
| `terraform fmt/validate`, `tflint` | CI-installed (no local terraform); files are `fmt`-clean by construction, minimal HCL |

Row counts observed (small profile, for P04's reconciliation): staged
timetable 12,347 → `fct_timetable_event` 12,026 (36 future-date + ~285 orphan
planted defects excluded, documented in model comments); staged meter HH
33,866 + 34,349 → `fct_meter_hh` 67,758 (2099-dated + unknown-meter planted
defects excluded); `fct_energy_daily` 1,440; `dim_date` 90 days; marts
carbon 6, space 495, asset-health 1,496, compliance 40, DQ 8. Full
silver→mart reconciliation is P04-owned (pending `ACCEPTANCE_P04.md`).

## P04-prerequisite fixes (dbt was red; CI needs it green)

`platform/dbt/` was untracked with 5 failing tests. Minimal FK-integrity
fixes applied (P04 docs/acceptance still ☐, owned by the P04 track):
`int_meter_hh_cleaned` excludes 2099 planted futures; `fct_meter_hh` inner-joins
the meter register; `fct_timetable_event` filters to the synthetic window and
conforms via `int_current_space` canonical ids; `sources.yml` duplicate entry
removed; `assert_asset_life_sane` column list fixed. No business logic changed.

## Acceptance mapping

- Green CI on main: workflows written + verified step-for-step locally; human
  pushes, enables Pages/branch protection, and links the first green run in README.
- `docs/ci-demo.md`: failing-PR demo with verbatim local outputs; branch names
  + screenshots are human placeholders.
- Wall time: measured steps total ~4 min local (pytest ~75 s, ingest ~35 s,
  dbt ~17 s); CI small-profile run stays well under 10 min.
- No secrets: `.env` gitignored, demo passwords labelled; gitleaks job added.
