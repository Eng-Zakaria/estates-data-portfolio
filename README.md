# Estates Data Portfolio (synthetic)

> **All data in this portfolio is synthetic or from public open sources. No real university, building performance, or compliance status is implied. Every chart carries a "Synthetic data for portfolio demonstration" footer.**

A portfolio of 20 data projects demonstrating University Estates Data Analyst skills: pipelines, space/asset/meter/BIM integration, Power BI reporting, data quality, standards, sustainability.

## Layout

- `AGENTS.md` — agent rules, layout, workflow
- `docs/specs/` — per-project specs (copied from prompts)
- `docs/PLAN.md` — foundation build plan
- `docs/DATA_MODEL.md` — truth model ER + export map
- `docs/OPEN_QUESTIONS.md` — gaps for the human
- `packages/campus_synth/` — **foundation generator (built first)**
- `platform/`, `projects/`, `infra/` — P01–P20 (not started; see STATUS.md)
- `data/` — gitignored generated outputs (`raw/`, `truth/`, `raw_snapshots/`)

## Quick start (foundation)

```bash
pip install -e ".[dev]"
make data                      # small profile: generate + ground truth
make snapshots                 # 12 weekly snapshots (P03 trend)
make test                      # pytest
make ci                        # lint + type + test + small generate
```

Full profile (~40 buildings, 24 months):

```bash
make data PROFILE=default
```

CLI directly:

```bash
python -m campus_synth.cli generate --profile small --seed 42 --out data/raw --defects 0.03
python -m campus_synth.cli truth --out data/raw/ground_truth.yaml
python -m campus_synth.cli snapshots --weeks 12 --out data/raw_snapshots
```

## Status

See `STATUS.md`. Foundation is the only project in progress.

## Provenance

See `DATA.md`. Foundation uses no external datasets — 100% synthetic via `campus_synth`.
Later projects will add public sources with licence/URL/version in `DATA.md`.
