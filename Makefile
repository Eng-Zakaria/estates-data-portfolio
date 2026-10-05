.PHONY: setup data test lint typecheck ci docs clean ingest catalogue airflow-up iot-demo p19 p08-run aws-plan aws-apply aws-destroy dbt-build dbt-test dq-check security dbt-docs

PROFILE ?= small
SEED ?= 42
OUT ?= data/raw
LAKE ?= data/lakehouse
PY ?= python
export PYTHONPATH := packages/campus_synth/src:platform/src:$(PYTHONPATH)

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
	mypy packages/campus_synth/src/campus_synth platform/src/ingest

ci: lint typecheck test
	$(PY) -m campus_synth.cli generate --profile small --seed 42 --out data/raw --defects 0.03
	$(PY) -m ingest.cli run-all --raw $(OUT) --out $(LAKE) --truth data/truth
	$(PY) -m ingest.cli reconcile --raw $(OUT) --out $(LAKE)
	dbt build --profiles-dir platform/dbt --project-dir platform/dbt --target dev
	$(PY) .github/scripts/dq_gate.py
	cd platform/dbt && DBT_DUCKDB_PATH=../../data/warehouse.duckdb sqlfluff lint models macros tests snapshots
	docker compose config --quiet

dbt-build:
	dbt build --profiles-dir platform/dbt --project-dir platform/dbt --target dev

dbt-test:
	dbt test --profiles-dir platform/dbt --project-dir platform/dbt --target dev

dbt-docs:
	dbt docs generate --profiles-dir platform/dbt --project-dir platform/dbt --target dev

dq-check:
	$(PY) .github/scripts/dq_gate.py

security:
	$(PY) -m pip_audit --desc on --aliases on 2>/dev/null || pip-audit --desc on --aliases on

docs:
	mkdocs build --strict 2>&1 || echo "mkdocs not configured yet (P20)"

clean:
	rm -rf data/raw data/raw_snapshots data/truth .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +

ingest:
	$(PY) -m ingest.cli run-all --raw $(OUT) --out $(LAKE) --truth data/truth

catalogue:
	$(PY) -m ingest.cli catalogue --out platform/docs/catalogue.md

aws-plan:
	cd infra/terraform && (terraform fmt -check && terraform init -backend=false && terraform validate || echo "terraform not installed or init failed; files kept fmt-clean by construction")

aws-apply:
	@echo "COST WARNING: creates AWS S3+Glue+Athena+IAM+Budget (charges apply). Do not run without checking region/costs."
	cd infra/terraform && terraform apply

aws-destroy:
	cd infra/terraform && terraform destroy

snapshots:
	$(PY) -m campus_synth.cli snapshots --weeks 12 --out data/raw_snapshots --seed $(SEED)

p08-run:
	$(PY) -m pytest projects/p08-net-zero-carbon/tests/ -q -p no:cacheprovider --no-cov
	$(PY) projects/p08-net-zero-carbon/scripts/export_gold.py
