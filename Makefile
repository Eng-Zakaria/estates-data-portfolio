.PHONY: setup data test lint typecheck ci docs clean ingest airflow-up iot-demo p19

PROFILE ?= small
SEED ?= 42
OUT ?= data/raw
PY ?= python
export PYTHONPATH := packages/campus_synth/src:$(PYTHONPATH)

setup:
	$(PY) -m pip install -e ".[dev]"

data:
	$(PY) -m campus_synth.cli generate --profile $(PROFILE) --seed $(SEED) --out $(OUT) --defects 0.03
	# generate already writes $(OUT)/ground_truth.yaml (planted + defect log).
	# `truth` is a standalone re-emit (planted only); do not overwrite the defect log here.

test:
	$(PY) -m pytest -q

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy packages/campus_synth/src/campus_synth

ci: lint typecheck test
	$(PY) -m campus_synth.cli generate --profile small --seed 42 --out data/raw --defects 0.03

docs:
	mkdocs build --strict 2>&1 || echo "mkdocs not configured yet (P20)"

clean:
	rm -rf data/raw data/raw_snapshots data/truth .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +

ingest:
	@echo "P01 ingest not yet implemented (foundation only)"

snapshots:
	$(PY) -m campus_synth.cli snapshots --weeks 12 --out data/raw_snapshots --seed $(SEED)
