# Reference index

Where everything else in the portfolio lives. Paths are relative to the repository root. They are written as paths, not links, because this site is built from its own folder and a link outside it would break the build.

## Platform: the shared foundation

| Path | What it is |
|---|---|
| `packages/campus_synth/` | the synthetic campus data generator: buildings, spaces, assets, meters, sensors, work orders, inspections, timetable, plus planted defects and a ground-truth file |
| `platform/src/ingest/` | landing, bronze, silver and quarantine: loads raw files, reconciles counts, records provenance |
| `platform/dbt/` | the transformation project: staging, intermediate, marts, tests, seeds, snapshots |
| `platform/contracts/` | data contracts for the source feeds, describing columns, grain and expectations |
| `platform/quality/` | the data quality framework: check definitions by dataset and the CLI that runs them |
| `platform/orchestration/` | Airflow DAGs for the pipeline, with pools and retries |
| `platform/docs/catalogue.md` | the raw-data catalogue |
| `platform/refs/` | reference notes used while building |

## Projects

| Project | Folder | What it produces |
|---|---|---|
| P06 space utilisation | `projects/p06-space-utilisation/` | utilisation mart analysis, Power BI handoff, validation SQL |
| P07 assets and maintenance | `projects/p07-asset-maintenance/` | KPI functions, backlog and reliability SQL, findings |
| P08 energy and carbon | `projects/p08-net-zero-carbon/` | carbon methodology, factor fetch script, Power BI handoff |
| P09 compliance | `projects/p09-compliance-tracker/` | status mart logic, remedial actions, weekly digest |
| P10 institutional return | `projects/p10-institutional-return/` | mock monthly return pack and validation output |
| P11 IFC analytics | `projects/p11-ifc-analytics/` | IFC to tables extractor, QA report, reconciliation |
| P12 COBie validator | `projects/p12-cobie-validator/` | COBie rules engine, seeded-error reporting, handover loader |
| P13 Uniclass mapper | `projects/p13-uniclass-mapper/` | classification mapper (development placeholder code list) |
| P14 ISO 19650 checker | `projects/p14-iso19650-checker/` | information naming and container state checks, conventions |
| P15 BMS and IoT | `projects/p15-bms-iot/` | broker, simulator, TimescaleDB schema, dashboards config |
| P16 energy anomalies | `projects/p16-energy-anomaly/` | anomaly findings on meter data (in progress) |
| P17 air quality and occupancy | `projects/p17-air-quality-occupancy/` | ventilation, comfort, occupancy, sensor health analyses |
| P18 digital twin layer | `projects/p18-digital-twin-layer/` | canonical ids, crosswalk, relationships, Brick model, REST API |
| P19 spatial and carbon map | `projects/p19-spatial-carbon-map/` | footprints from OpenStreetMap, carbon choropleth, isochrones |
| P20 governance and literacy | `projects/p20-governance-literacy/` | this site |

## Repository-level documents

| Path | What it is |
|---|---|
| `AGENTS.md` | the rules every project in the portfolio follows |
| `STATUS.md` | what is built, what is evidenced, what is missing |
| `DATA.md` | provenance: every external dataset, standard, code list and factor, with licence and retrieval date |
| `docs/OPEN_QUESTIONS.md` | gaps that need a human, such as a standard we could not obtain |
| `docs/dq-policy.md` | the authoritative data quality policy: dimensions, severities, thresholds, response times |
| `docs/DATA_MODEL.md` | the warehouse layers and the grain of each table |
| `docs/PORTFOLIO_REPORT.md` | the narrative summary of the portfolio |
| `docs/adr/` | architecture decision records |
| `docs/ACCEPTANCE_*.md` | the acceptance evidence for the foundation and the platform projects |
| `docs/PLAN_P*.md` | the plan written before each project was built |
| `mkdocs.yml` | the portfolio-level documentation site |
| `Makefile` | `make data`, `make ci`, and one target per project |

## Standards and licences

Anything taken from outside the portfolio is recorded in `DATA.md` with its URL, licence, version and retrieval date. Standards text is not reproduced anywhere: the [standards register](generated/standards-register.md) links to the official source and records how far the implementation honestly goes.

OpenStreetMap geometry used by P19 is licensed ODbL with attribution, and the government emission factors are Open Government Licence v3.0. Both are recorded in `DATA.md`.

## Generated data in this checkout

The synthetic data is not committed: `make data` rebuilds it from the generator with a fixed seed. Artefacts that other projects write live under `data/` (git ignored), and each project documents where its outputs land.