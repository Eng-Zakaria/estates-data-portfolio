.PHONY: setup data eval review test thresholds lint clean

PY ?= python
export PYTHONPATH := src:$(PYTHONPATH)

setup:
	$(PY) -m pip install -e "."

data:
	$(PY) -m anomaly.cli fetch-bdg2

eval:
	$(PY) -m anomaly.cli evaluate --out outputs

review:
	$(PY) -m anomaly.cli review-bdg2 --out outputs/bdg2

thresholds:
	$(PY) scripts/threshold_separation.py

test:
	$(PY) -m pytest tests -q

lint:
	ruff check src tests scripts; ruff format --check src tests scripts

clean:
	rm -rf outputs __pycache__ .pytest_cache
