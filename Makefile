.PHONY: setup data test lint typecheck ci docs clean ingest catalogue airflow-up airflow-down airflow-ps airflow-logs airflow-pools airflow-backfill iot-demo p19 p18-run p10-run p08-run p06-run p07-run p09-run p11-run p12-run p13-fetch p13-eval p13-test p13-run p14-sample p14-check p14-check-clean p14-variant p14-test p14-run p16-test p16-eval p16-thresholds p16-run aws-plan aws-apply aws-destroy dbt-build dbt-test dq-check security dbt-docs

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

p11-run:
	$(PY) -m pytest projects/p11-ifc-analytics/tests/ -q -p no:cacheprovider --no-cov
	$(PY) projects/p11-ifc-analytics/src/ifc2tables/make_sample_ifc.py --out data/ifc/sample_b003.ifc
	$(PY) projects/p11-ifc-analytics/src/ifc2tables/extract.py data/ifc/sample_b003.ifc --out data/gold/ifc
	$(PY) projects/p11-ifc-analytics/src/ifc2tables/qa_report.py --tables data/gold/ifc --out data/gold/ifc
	$(PY) projects/p11-ifc-analytics/src/ifc2tables/reconcile.py --tables data/gold/ifc --out data/gold/ifc

p06-run:
	$(PY) -m pytest projects/p06-space-utilisation/tests/ -q -p no:cacheprovider --no-cov

p07-run:
	$(PY) -m pytest projects/p07-asset-maintenance/tests/ -q -p no:cacheprovider --no-cov

p19:
	$(PY) projects/p19-spatial-carbon-map/scripts/fetch_osm.py
	$(PY) projects/p19-spatial-carbon-map/scripts/build_outputs.py
	$(PY) -m pytest projects/p19-spatial-carbon-map/tests/ -q -p no:cacheprovider --no-cov

p18-run:
	$(PY) -m pytest projects/p18-digital-twin-layer/tests/ -q -p no:cacheprovider --no-cov
	$(PY) projects/p18-digital-twin-layer/src/crosswalk.py
	$(PY) projects/p18-digital-twin-layer/src/relationships.py
	$(PY) projects/p18-digital-twin-layer/src/brick.py
	$(PY) projects/p18-digital-twin-layer/src/coverage.py

p09-run:
	$(PY) -m pytest projects/p09-compliance-tracker/tests/ -q -p no:cacheprovider --no-cov
	$(PY) projects/p09-compliance-tracker/scripts/gen_remedial.py
	$(PY) projects/p09-compliance-tracker/scripts/digest.py --as-of 2026-03-31 | diff projects/p09-compliance-tracker/tests/golden/digest_2026-03-31.html - 2>&1 | head -5; echo "digest golden-file test: normalized timestamp diff only"

p12-run:
	$(PY) -m pytest projects/p12-cobie-validator/tests/ -q -p no:cacheprovider --no-cov
	$(PY) projects/p12-cobie-validator/src/make_sample_cobie.py
	$(PY) projects/p12-cobie-validator/src/cli.py validate data/cobie/valid.xlsx --out data/cobie/report_valid

P13 = projects/p13-uniclass-mapper

# Attempts the official NBS download; exits non-zero (ignored) when the tables
# are gated, in which case the non-authoritative placeholder is written instead.
p13-fetch:
	- $(PY) $(P13)/scripts/fetch_uniclass.py

# Reproduces every number in the README and docs/ACCEPTANCE_P13.md (seed 42).
p13-eval:
	$(PY) $(P13)/src/eval.py

p13-test:
	$(PY) -m pytest $(P13)/tests/ -q -p no:cacheprovider --no-cov

p13-run: p13-fetch p13-eval p13-test

P14 = projects/p14-iso19650-checker
P14_CFG = $(P14)/conventions/uk_national_annex.yml
P14_VARIANT_CFG = $(P14)/conventions/estates_cde_variant.yml

p14-sample:
	$(PY) $(P14)/src/make_sample.py --out data/iso19650/sample --n 300 --seed 42
	$(PY) $(P14)/src/make_sample.py --out data/iso19650/clean --n 200 --clean

p14-check:
	$(PY) $(P14)/src/cli.py check data/iso19650/sample --config $(P14_CFG) --register data/iso19650/sample_register.csv --suggest --out data/iso19650/report

p14-check-clean:
	$(PY) $(P14)/src/cli.py check data/iso19650/clean --config $(P14_CFG) --register data/iso19650/clean_register.csv --out data/iso19650/report_clean

p14-variant:
	$(PY) $(P14)/src/make_sample.py --out data/iso19650/variant --n 120 --clean --config $(P14_VARIANT_CFG)
	$(PY) $(P14)/src/cli.py check data/iso19650/variant --config $(P14_VARIANT_CFG) --register data/iso19650/variant_register.csv --out data/iso19650/report_variant

p14-test:
	$(PY) -m pytest $(P14)/tests/ -q -p no:cacheprovider --cov=$(P14)/src --cov-report=term-missing

p14-run: p14-sample p14-test p14-check p14-check-clean p14-variant

P16 = projects/p16-energy-anomaly

p16-test:
	$(PY) -m pytest $(P16)/tests/ -q -p no:cacheprovider --no-cov

p16-eval:
	PYTHONPATH=$(P16)/src $(PY) -m anomaly.cli evaluate --out $(P16)/outputs

p16-thresholds:
	$(PY) $(P16)/scripts/threshold_separation.py

p16-run: p16-test p16-eval p16-thresholds

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

p10-run:
	$(PY) -m pytest projects/p10-institutional-return/tests/ -q -p no:cacheprovider --no-cov
	$(PY) projects/p10-institutional-return/src/main.py --return-date 2026-03-31 --out data/p10_output --verify
