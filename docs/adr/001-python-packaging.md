# ADR-001: Python version and packaging layout

Date: 2026-10-03. Status: accepted.

## Context

Spec defaults to Python 3.12 with `uv`. Dev machine provides Python 3.13; CI images commonly offer 3.11/3.12.

## Decision

- Require `>=3.11` in `pyproject.toml`; code avoids 3.12-only syntax. CI matrix covers 3.11/3.12 (3.13 compatible locally).
- Single root `pyproject.toml` with `packages/campus_synth/src/campus_synth` via hatch `force-include` (`campus_synth` import name) plus `pytest.pythonpath` for dev. Avoids dual-pyproject drift for the foundation; revisit if P02/P15 need separate services.

## Consequences

- `pip install -e ".[dev]"` works on 3.11–3.13. `uv.lock` generation deferred to networked CI (pinned ranges in `pyproject.toml` meanwhile).
