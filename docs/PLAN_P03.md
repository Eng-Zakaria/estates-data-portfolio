# PLAN: P03 Data quality framework (YAML to GX + SQL, scoring, trend, alerts)

## Goal
YAML-declared checks (`platform/quality/checks/*.yml`) compiled to GX expectation
suites (verified GX 1.23.2 API, see below) + a DuckDB SQL engine for high-volume
and statistical checks. Results in `dq.*` tables, weighted scores, 12-week trend,
alerts, GX Data Docs, dq-policy, Power BI scorecard handoff. All synthetic.

## GX 1.23.2 API verification (empirical, 2026-10-05, NOT from memory)
- `pip install great-expectations` gives 1.23.2. `gx.get_context(mode='file'|'ephemeral')` ok.
- Pandas source: `context.data_sources.add_pandas(name)` then
  `add_dataframe_asset(name)` then `add_batch_definition_whole_dataframe(name)` ok.
- Runtime frame: `asset.build_batch_request(options={'dataframe': df})` (exactly
  one key `dataframe`); `asset.get_batch(...)` or `ValidationDefinition.run(
  batch_parameters={'dataframe': df})` ok. (`asset.build_batch_parameters`
  does NOT exist; `Checkpoint.run()` takes NO `result_format`.)
- Suite: `gx.ExpectationSuite(name)` + `suite.add_expectation(gx.expectations.X(...))`
  + `context.suites.add(suite)`; VD must be added via
  `context.validation_definitions.add(vd)` before run (else freshness error).
- `vd.run(...)` gives `.success`, `.statistics`, per-result `unexpected_count`;
  `result_format=COMPLETE` + `partial_unexpected_count=100` gives up to 100 samples.
- `context.build_data_docs()` renders validations to `.../data_docs/local_site`.
- Perf: 4 expectations x 774k sensor rows about 2 s (pandas). Default profile is
  much bigger, so row-heavy tables go to the SQL engine (same YAML, same
  results schema); GX covers registers and transactions. Decision recorded here.

## Architecture
```
checks/*.yml --spec.py--+--gxcompile.py-- GX suites --gxrun.py-- results
                        +--sqlchecks.py-- DuckDB --------------+
results --store.py-- data/quality.duckdb (dq.results, dq.failed_rows,
  dq.scores, dq.runs, dq.alerts) + data/quality/gold/*.parquet+csv
recall.py: ground_truth.yaml x quarantine + silver-check mapping gives recall/type
trend.py: spaces checks x 12 snapshots gives dq.scores history; alerts.py
docs: GX Data Docs (artifact) + dq-policy.md + powerbi/ handoff + validation SQL
```

## Engine split (principled, documented in README)
- GX: register and transaction tables (spaces, assets, work orders, inspections,
  timetable, meter grain/units, sensor nulls/uniqueness). Full rows.
- SQL (DuckDB, same YAML, same results schema): high-volume row checks
  (sensors/BMS/meters), statistics GX cannot express (flat-line runs, spikes vs
  rolling median, DST period counts, gap runs, volume +-3sigma, reconciliation
  equality, quarantine recall rates, explained rates).

## Recall design (grounded in generator + silver code, not guessed)
Read `packages/campus_synth/src/campus_synth/defects.py` (injection order and
targets), `exports.py` (per-table column order: nulls hit col[1], out_of_range
hits first numeric, misspelt hits first object col, orphans append B999 rows),
and `platform/src/ingest/silver_*.py` (pipeline order decides which quarantine
reason a multi-hit row lands under). Rules in recall.py:
- exact-key types (WO/EV/room/IN ids): planted key in quarantine key-col (any
  reason; overlap-safe) or in mapped silver-leak check failures.
- masked keys (*-xx): count rule, silver xx-failures + quarantine xx rows.
- space nulls: null-reason rows + blank-row absence rule (blank never reaches raw).
- space misspelt: keys absent from bronze (per-campus sheet filter drops them).
- meter/sensor repeated keys: key presence (sensors) or grain-excess + reason
  counts (meters); gaps via P01 gaps report max; mB wide-format x48 multipliers.
- Tier 2 (only for types under 100%): bronze cross-match to prove
  overlap containment, else report the honest shortfall.

## Scoring (documented in dq-policy.md)
score(dataset) = 100 * sum(w * pass_rate) / sum(w), w: error=3, warn=2, info=1.
Status: pass iff pass_rate >= threshold (error fail turns the CI gate red).
Dimension scores group by dimension; building scores from `by_building` checks.
Alerts: drop over 5 pts vs trailing-7-run mean, or any error fail, go to dq.alerts.

## Risks and mitigations
- Shared tree: another session is active on P06/P04. P03 uses NEW files only
  until the final step; shared edits (Makefile, STATUS, DATA, pyproject) last,
  with a commit per milestone so work is never lost again (2026-10-05 reset
  wiped uncommitted P03 work once).
- DuckDB single-writer locks: own store `data/quality.duckdb`, never warehouse.duckdb.
- Lakehouse churn underfoot: record input mtimes/hashes in dq.runs provenance.
- GX telemetry flush errors: disable usage stats in GX config.
- Default-profile runtime: measure on small, extrapolate; SQL engine for heavy tables.

## Acceptance mapping
- Recall per type from recall.py (quarantine + mapped silver-check detections).
- Clean run (defects=0 into separate raw/lake dirs): zero error failures.
- Runtime measured on small + default-profile note.
- 80%+ coverage on quality modules; pass+fail fixture per SQL check.
