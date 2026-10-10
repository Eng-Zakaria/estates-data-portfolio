# P20 governance and literacy pack — local targets.
#
# The portfolio-level targets (make p20-run, make p20-check) call these.
# Run from the repository root; PY must resolve to the project interpreter.

PY ?= python
P20 = projects/p20-governance-literacy
MKDOCS_YML = $(P20)/mkdocs.yml

.PHONY: build check test readability coverage links site serve clean

## Regenerate the generated pages from dbt, the DQ output and the YAML sources.
build:
	$(PY) $(P20)/src/cli.py build

## Every gate: registry, glossary coverage, staleness, links, readability.
check:
	$(PY) $(P20)/src/cli.py check

## Unit tests (fixtures first, then the real repository).
test:
	$(PY) -m pytest $(P20)/tests -q -p no:cacheprovider --no-cov

## Measured readability per plain-English page.
readability:
	$(PY) $(P20)/src/cli.py readability

## Registry and glossary coverage of dashboard KPIs.
coverage:
	$(PY) $(P20)/src/cli.py coverage

## In-site link and anchor report.
links:
	$(PY) $(P20)/src/cli.py links

## Strict site build (warnings become errors).
site:
	$(PY) -m mkdocs build --strict -f $(MKDOCS_YML)

## Serve the site locally at http://127.0.0.1:8000/
serve:
	$(PY) -m mkdocs serve -f $(MKDOCS_YML)

clean:
	rm -rf $(P20)/site .pytest_cache
	find $(P20) -type d -name __pycache__ -prune -exec rm -rf {} +