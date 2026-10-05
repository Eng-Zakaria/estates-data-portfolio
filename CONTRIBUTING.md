# Contributing (P05)

## Branching

- `main` is protected (see `docs/branch-protection.md`). Work on short-lived
  branches: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- Open a PR against `main`; the PR template checklist must be complete.
  Green CI is required before merge (no admin overrides for red data gates).

## Conventional commits

`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `ci:` (release notes are generated
from these, see `release.yml`).

## Local gates (mirror CI)

```bash
pip install -e ".[dev]"
pre-commit install        # optional but recommended
make ci                   # lint + type + test + data + ingest + dbt-build + DQ gate
```

## Data rules (never break)

Synthetic or public data only; label synthetic outputs; record provenance in
`DATA.md`; never invent standard codes/factors (see `AGENTS.md` hard rules).
Generated `data/` and `*.parquet` are gitignored — use `make data`.
