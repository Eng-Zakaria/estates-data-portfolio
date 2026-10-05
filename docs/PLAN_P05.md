# PLAN: P05 CI/CD for data

## Goal
Harden CI/CD per `docs/specs/01-platform-p01-p05.md` §P05 so every PR/main push runs
lint + type + test + small-profile data → ingest → `dbt build` → DQ gate, plus
terraform/docker/airflow/docs checks, with nightly/security/docs/release workflows.

## Pre-requisite (P04 unblocks CI green)
`platform/dbt/` exists untracked with `dbt build` failing (5 errors, verified 2026-10-04).
CI cannot be green without a green `dbt build`, so P05 includes **minimal FK-integrity
fixes only** (no P04 docs/acceptance; P04 stays ☐):
1. `stg_tt__event`: strip leading `S-` from `space_id` (register uses `B001-L00-001`,
   timetable uses `S-B001-L00-001`; verified in warehouse).
2. `fct_meter_hh`: inner-join to known meters (planted `*-Exx`/`*-Gxx` meter_ids in
   silver have no truth register row; LEFT JOIN preserves orphans → relationships fail).
3. `fct_timetable_event` + `fct_meter_hh`: exclude far-future planted defects
   (`ts_utc`/`event_date` in 2099; synthetic window ends 2026-03-31).
4. `dim_date`: date spine = calendar seed min/max ±30d buffer (covers legitimate
   trailing 2026-04-01 meter dates, excludes 2099).
5. `assert_asset_life_sane`: selects `expected_life_years`, absent from
   `mart_asset_health` → select available columns only.
All fixes documented in `docs/ACCEPTANCE_P05.md` as P04-prerequisite, reconciled
(silver→mart row deltas reported, never silently dropped without a note).

## Tasks
1. Commit `platform/dbt/` (minus `target/`, `logs/`) with fixes above; `.gitignore`
   += `platform/dbt/target/`, `platform/dbt/logs/`, `platform/dbt/dbt_packages/`, `logs/`.
2. `pyproject.toml`: pin `dbt-duckdb==1.10.1`, `sqlfluff==4.4.0` (+ `mkdocs-material`,
   `pip-audit`) in dev extras; document pins.
3. Rewrite `.github/workflows/ci.yml`: concurrency cancel; matrix py 3.11/3.12;
   uv cache; ruff; mypy; pytest + ≥80% gate; `make data` (small) → `make ingest` →
   reconcile → `dbt build`; DQ gate script (runs when `platform/quality/` exists,
   else skip-notice = P03 hook); sqlfluff; terraform fmt/validate (+tflint);
   `docker compose config`; Airflow DagBag (skip-notice until P02); `mkdocs build --strict`.
4. New workflows: `nightly.yml` (full profile + artifacts + create-issue-on-fail),
   `docs.yml` (Pages: mkdocs + dbt docs; GX hook), `release.yml` (tag `v*`: build +
   changelog + artifacts), `security.yml` (pip-audit, gitleaks, CodeQL) +
   `_reusable.yml` (lint+test callable) + `dependabot.yml`.
5. `.pre-commit-config.yaml` mirroring CI; PR template; CODEOWNERS; `CONTRIBUTING.md`;
   `docs/branch-protection.md`; README badges + status refresh.
6. Minimal `mkdocs.yml` (+ `docs/index.md`) so `mkdocs build --strict` is green.
7. `Makefile`: `ci` = lint + type + test + data + ingest + dbt-build + dq-check;
   new targets `dbt-build`, `dq-check` (skip-notice until P03), `security`.
8. `docs/ci-demo.md` (failing-PR demo w/ local evidence + human screenshot placeholders),
   `docs/ACCEPTANCE_P05.md` (evidence per acceptance bullet), STATUS.md tick, DATA.md note.

## Risks
- mypy broken locally (`pathspec.patterns.gitignore` missing) → env-only; fix with
  `pip install -U pathspec`; CI uses fresh env.
- terraform/gitleaks/mkdocs absent locally → CI installs via actions; local verify
  via `make aws-plan` fallback + `docker compose config` + pip-installed mkdocs.
- `dbt build` on full profile slower; nightly only, CI stays small-profile (<10 min).
- sqlfluff `dbt` templater needs `dbt` importable in pre-commit/CI → install order noted.

## Open questions
- P02/P03 steps are skip-notices until those projects land (tracked here, not silent).
- `uv.lock` is gitignored (see `.gitignore:18`) despite AGENTS.md pinning guidance;
  left as-is, recorded for P20 governance.
- Pages deployment needs human to enable Pages + required checks (see branch-protection doc).
