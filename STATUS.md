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
| P07 | Asset & maintenance | ☑ done | 2026-10-08 | acceptance: projects/p07-asset-maintenance/docs/ACCEPTANCE_P07.md — 7 tests, 5 validation SQL, RLS + test cases, bad-actors top-10 (B012 plant default-only, reported) |
| P08 | Net zero & carbon | ✅ done | 2026-10-05 | acceptance MISSING (review) — 7 tests, 4 validation SQL, PBI handoff |
| P09 | Compliance tracker | ✅ done | 2026-10-05 | acceptance MISSING (review) — 11 tests, digest golden, 5 validation SQL, PBI |
| P10 | Mock institutional return | ✅ done | 2026-10-06 | acceptance + SPEC MISSING (review) — 10 tests, deterministic re-run |
| P11 | IFC - analytics | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P11.md — 6 tests, 0.12s extract, QA finds all planted defects, recon 31 matched/12 mismatches, powerbi handoff added |
| P12 | COBie validator & loader | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P12.md — 17 tests, 42 seeded events 100% category recall, valid 100/corrupt 39.0, loader 8→unchanged |
| P13 | Uniclass mapper | ✅ done | 2026-10-08 | acceptance: docs/ACCEPTANCE_P13.md — 20 tests, hybrid 97.81% top-1 / 99.56% top-3 on test (n=228) vs fuzzy 21.49% / embedding 57.02%; dev-tuned τ_high 0.30 → 98.40% auto-accept precision; review loop 78.61%→98.93% on dev; metrics byte-identical across 2 runs. **Open: official NBS tables not obtained — placeholder + `is_mock` + `--final` refusal; human review of review_sample.csv (265 rows, 0 done) outstanding** (docs/OPEN_QUESTIONS.md §2) |
| P14 | ISO 19650 checker | ✅ done | 2026-10-07 | acceptance: projects/p14-iso19650-checker/docs/ACCEPTANCE_P14.md — convention verified from CDBB National Annex + UK BIM Framework Part C (quoted in docs/SOURCES.md); 83 tests, 94% cov, 20 rule ids, 301-file sample 94.0% compliant, clean sample 0 false positives, config swap 0 vs 1320 errors, apply+rollback reversible |
| P15 | BMS/sensor ingestion | 🚧 partial | | scaffold only (compose/grafana/schema/simulator); no README/tests/docs/acceptance |
| P16 | Energy anomaly detection | ✅ done | 2026-10-08 | acceptance: docs/ACCEPTANCE_P16.md — 36 tests, 210 injected faults scored per method/type, planted B007 #1 (£7817.23) & B019 #2 (£815.37), BDG2 (CC-BY, md5-verified) top-6 review pack no accuracy claimed, PBI handoff + 4 validation SQL; overnight threshold does NOT transfer across profiles (0 FP small vs 21/58 FP default) — measured, documented, open |
| P17 | Air quality & occupancy | ✅ done | 2026-10-06 | acceptance: docs/ACCEPTANCE_P17.md — 38 tests; README/SPEC MISSING (review) |
| P18 | Digital twin data layer | ✅ done | 2026-10-06 | acceptance MISSING (review) — crosswalk, Brick SHACL, FastAPI, coverage; README present |
| P19 | Spatial analysis | ✅ done | 2026-10-05 | acceptance MISSING (review) — OSM+synthetic, 10 tests, outputs; README present |
| P20 | Governance & literacy pack | ☐ | | not started |
