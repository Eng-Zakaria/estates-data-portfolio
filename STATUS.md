# STATUS.md

> Acceptance = `docs/ACCEPTANCE_Pxx.md` (or `projects/pNN-*/docs/ACCEPTANCE_PNN.md`) exists — the
> AGENTS.md evidence rule. ✅ = done AND accepted. Rows marked "acceptance MISSING (review)"
> are built and evidenced in their README but still need an acceptance doc.

| ID | Project | Status | Date | Notes / evidence |
|---|---|---|---|---|
| F | Foundation campus_synth | ✅ done | 2026-10-03 | acceptance: docs/ACCEPTANCE_F.md — 20 tests, 96% cov, 17–20s |
| P01 | Campus data warehouse | ✅ done | 2026-10-04 | acceptance: docs/ACCEPTANCE_P01.md — 7 tests, ingest 35s, 8/8 reconciled |
| P02 | Orchestrated ETL (Airflow) | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P02.md — 7 DAGs, corrupt→quarantine+Mailpit, 30-run CSV |
| P03 | Data quality framework | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P03.md — 133 checks, recall 100%, 51 tests |
| P04 | dbt project | ✅ done | 2026-10-05 | acceptance: docs/ACCEPTANCE_P04.md — 196 pass/0 err, 147+2 tests |
| P05 | CI/CD for data | ✅ done | 2026-10-05 | acceptance: docs/ACCEPTANCE_P05.md — workflows verified locally |
| P06 | Space utilisation | ✅ done | 2026-10-05 | acceptance MISSING (review) — 7 tests, 5 validation SQL, PBI handoff |
| P07 | Asset & maintenance | ✅ done | 2026-10-08 | acceptance: projects/p07-asset-maintenance/docs/ACCEPTANCE_P07.md — 7 tests, 5 validation SQL, RLS + test cases, bad-actors top-10 |
| P08 | Net zero & carbon | ✅ done | 2026-10-05 | acceptance MISSING (review) — 7 tests, 4 validation SQL, PBI handoff |
| P09 | Compliance tracker | ✅ done | 2026-10-05 | acceptance MISSING (review) — 11 tests, digest golden, 5 validation SQL, PBI |
| P10 | Mock institutional return | ✅ done | 2026-10-06 | acceptance + SPEC MISSING (review) — 10 tests, deterministic re-run |
| P11 | IFC → analytics | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P11.md — 6 tests, QA finds all planted defects, recon 31/12, PBI handoff |
| P12 | COBie validator & loader | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P12.md — 17 tests, 42 seeded events 100% category recall, loader idempotent |
| P13 | Uniclass mapper | ✅ done | 2026-10-08 | acceptance: docs/ACCEPTANCE_P13.md — 20 tests, hybrid 97.81% top-1 vs fuzzy 21.49%; **open: official NBS tables not obtained (placeholder + `--final` refusal), human review of review_sample.csv outstanding** |
| P14 | ISO 19650 checker | ✅ done | 2026-10-07 | acceptance: projects/p14-iso19650-checker/docs/ACCEPTANCE_P14.md — 83 tests, 94% cov, 20 rules, convention verified from CDBB National Annex |
| P15 | BMS/sensor ingestion | ✅ built, ⚠ live stack unverified | 2026-10-10 | acceptance: docs/ACCEPTANCE_P15.md — 245 tests, 95% cov, 84,435/84,435 valid messages ingested (100.0000%), 141 dead-lettered, 20/20 planted faults detected (SEM-01/02/03/05 + STALENESS), clean plant = 0 findings / 0 unhealthy, ruff + mypy clean. **Docker engine unavailable: `make iot-up` / `iot-demo`, Grafana render, flow import and the schema migration against a live TimescaleDB are all unverified** — full list in acceptance §7, human action in docs/OPEN_QUESTIONS.md. Spec deviations in SPEC.md (equipment segment added to topics; CSV rather than Parquet export; BACpypes3 device not built) |
| P16 | Energy anomaly detection | ✅ done | 2026-10-08 | acceptance: docs/ACCEPTANCE_P16.md — 36 tests, 210 injected faults, B007 #1 / B019 #2, BDG2 review pack; overnight threshold does not transfer across profiles (measured) |
| P17 | Air quality & occupancy | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P17.md — 38 tests; README/SPEC MISSING (review) |
| P18 | Digital twin data layer | ✅ done | 2026-10-06 | acceptance MISSING (review) — crosswalk, Brick SHACL, FastAPI, coverage; README present |
| P19 | Spatial analysis | ✅ done | 2026-10-05 | acceptance MISSING (review) — OSM+synthetic, 10 tests, outputs; README present |
| P20 | Governance & literacy pack | ✅ done | 2026-10-10 | acceptance: docs/ACCEPTANCE_P20.md — 126 tests, 96% cov, 7 gates green, 69/69 dashboard KPIs in registry + glossary, 107 links clean, Flesch min 67.4 / mean 76.4 (target 50), mkdocs --strict clean; gaps: P16 excluded from the KPI scan (explicit + tested), external links not fetched, governance roles unratified |
