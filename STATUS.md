# STATUS.md

> Acceptance = `docs/ACCEPTANCE_Pxx.md` exists (AGENTS.md evidence rule). ✅ = done AND accepted.
> Projects marked ✅ with "acceptance MISSING" are built and evidenced in their README but need an acceptance doc.

| ID | Project | Status | Date | Notes / evidence |
|---|---|---|---|---|
| F | Foundation campus_synth | ✅ done | 2026-10-03 | acceptance: docs/ACCEPTANCE_F.md — 20 tests, 96% cov, 17–20s |
| P01 | Campus data warehouse | ✅ done | 2026-10-04 | acceptance: docs/ACCEPTANCE_P01.md — 7 tests, ingest 35s, 8/8 reconciled |
| P02 | Orchestrated ETL (Airflow) | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P02.md — 7 DAGs, corrupt→quarantine+Mailpit, 30-run CSV |
| P03 | Data quality framework | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P03.md — 133 checks, recall 100%, 51 tests |
| P04 | dbt project | ✅ done | 2026-10-05 | acceptance: docs/ACCEPTANCE_P04.md — 196 pass/0 err, 147+2 tests |
| P05 | CI/CD for data | ✅ done | 2026-10-05 | acceptance: docs/ACCEPTANCE_P05.md — workflows verified locally |
| P06 | Space utilisation | ✅ done | 2026-10-05 | acceptance MISSING (review) — 7 tests, 5 validation SQL, PBI handoff |
| P07 | Asset & maintenance | ☐ | | not started |
| P08 | Net zero & carbon | ✅ done | 2026-10-05 | acceptance MISSING (review) — 7 tests, 4 validation SQL, PBI handoff |
| P09 | Compliance tracker | ✅ done | 2026-10-05 | acceptance MISSING (review) — 11 tests, digest golden, 5 validation SQL, PBI |
| P10 | Mock institutional return | ✅ done | 2026-10-06 | acceptance + SPEC MISSING (review) — 10 tests, deterministic re-run |
| P11 | IFC - analytics | ? done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P11.md � 6 tests, 0.49s extract, QA finds all planted defects, recon 31 matched/12 mismatches, powerbi handoff added |
| P12 | COBie validator & loader | 🚧 partial | | code+rules+README+tests committed; SPEC/docs/acceptance/powerbi MISSING (review) |
| P13 | Uniclass mapper | 🔨 in progress | | src+tests UNCOMMITTED; no README/SPEC/acceptance; mock Uniclass placeholder |
| P14 | ISO 19650 checker | 🚧 partial | | code+conventions+README+tests committed; SPEC/docs/acceptance MISSING (review) |
| P15 | BMS/sensor ingestion | 🚧 partial | | scaffold only (compose/grafana/schema/simulator); no README/tests/docs/acceptance |
| P16 | Energy anomaly detection | 🔨 in progress | | src+tests UNCOMMITTED; no README/SPEC/acceptance |
| P17 | Air quality & occupancy | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P17.md — 38 tests; README/SPEC MISSING (review) |
| P18 | Digital twin data layer | ✅ done | 2026-10-06 | acceptance MISSING (review) — crosswalk, Brick SHACL, FastAPI, coverage; README present |
| P19 | Spatial analysis | ✅ done | 2026-10-05 | acceptance MISSING (review) — OSM+synthetic, 10 tests, outputs; README present |
| P20 | Governance & literacy pack | ☐ | | not started |
