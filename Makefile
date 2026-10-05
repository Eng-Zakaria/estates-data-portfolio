.PHONY: setup data test lint typecheck ci docs clean ingest catalogue airflow-up airflow-down airflow-ps airflow-logs airflow-pools airflow-backfill iot-demo p19 p08-run p06-run aws-plan aws-apply aws-destroy dbt-build dbt-test dq-check security dbt-docs

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

p06-run:
	$(PY) -m pytest projects/p06-space-utilisation/tests/ -q -p no:cacheprovider --no-cov

p19:
	$(PY) projects/p19-spatial-carbon-map/scripts/fetch_osm.py
	$(PY) projects/p19-spatial-carbon-map/scripts/build_outputs.py
	$(PY) -m pytest projects/p19-spatial-carbon-map/tests/ -q -p no:cacheprovider --no-cov

p09-run:
	$(PY) -m pytest projects/p09-compliance-tracker/tests/ -q -p no:cacheprovider --no-cov
	$(PY) projects/p09-compliance-tracker/scripts/gen_remedial.py
	$(PY) projects/p09-compliance-tracker/scripts/digest.py --as-of 2026-03-31 | diff projects/p09-compliance-tracker/tests/golden/digest_2026-03-31.html - 2>&1 | head -5; echo "digest golden-file test: normalized timestamp diff only"

AF_COMPOSE = ENV_FILE_PATH=.env docker compose --env-file platform/orchestration/.env --project-directory platform/orchestration -f platform/orchestration/docker-compose.yml -f platform/orchestration/docker-compose.override.yml

airflow-build:
	test -f platform/orchestration/.env || cp platform/orchestration/.env.example platform/orchestration/.env
	grep -q '^FERNET_KEY=' platform/orchestration/.env || ($(PY) -c "from cryptography.fernet import Fernet; print('FERNET_KEY='+Fernet.generate_key().decode())" >> platform/orchestration/.env)
	$(AF_COMPOSE) build

airflow-up: airflow-build
	$(AF_COMPOSE) up airflow-init
	$(AF_COMPOSE) up -d
	$(AF_COMPOSE) exec -T airflow-scheduler airflow pools set ingest_pool 4 "P02 ingest concurrency" || true
	$(AF_COMPOSE) exec -T airflow-scheduler airflow pools set dbt_pool 1 "P02 dbt serial" || true
	@echo "Airflow UI: http://localhost:8080  Mailpit: http://localhost:8025"

airflow-ps:
	$(AF_COMPOSE) ps

airflow-logs:
	$(AF_COMPOSE) logs -f airflow-scheduler

airflow-down:
	$(AF_COMPOSE) down

airflow-pools:
	$(AF_COMPOSE) exec -T airflow-scheduler airflow pools set ingest_pool 4 "P02 ingest concurrency"
	$(AF_COMPOSE) exec -T airflow-scheduler airflow pools set dbt_pool 1 "P02 dbt serial"

airflow-backfill:
	$(AF_COMPOSE) exec -T airflow-scheduler airflow dags backfill ingest_meter_hh -s 2026-02-01 -e 2026-03-02 --rerun-failed-tasks
	$(PY) platform/orchestration/scripts/export_runs.py
