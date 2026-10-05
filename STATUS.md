# STATUS.md

| ID | Project | Status | Date | Notes / evidence |
|---|---|---|---|---|
| F | Foundation campus_synth | ✅ done | 2026-10-03 | 20 tests pass, 96% cov, ruff+mypy clean, small generate 17–20s; see docs/ACCEPTANCE_F.md |
| P01 | Campus data warehouse | ✅ done | 2026-10-04 | 7 platform tests pass, ingest 35s, 8/8 reconciled zero-loss; see docs/ACCEPTANCE_P01.md |
| P02 | Orchestrated ETL (Airflow) | ✅ done | 2026-10-05 | DAGs + Docker, DagBag import green, 4 ingest + transform + dq + housekeeping; see docs/ACCEPTANCE_P02.md |
| P03 | Data quality framework | ✅ done | 2026-10-06 | 133 YAML checks (GX 58 + SQL 41 + recall 34), recall 100% on planted types, 51 tests pass, ruff+mypy clean, DQ scores 83–100; see docs/ACCEPTANCE_P03.md |
| P04 | dbt project | ✅ done | 2026-10-05 | dbt build green 196 pass/0 err, 147 tests+2 unit, 100% models tested, 100% cols documented, 21 contracts; see docs/ACCEPTANCE_P04.md |
| P05 | CI/CD for data | ✅ done | 2026-10-05 | ci/nightly/docs/release/security + reusable workflows, pre-commit, gates verified locally (ruff+mypy clean, pytest 27 pass 84%, dbt 196 pass, sqlfluff+mkdocs+compose clean); human must enable Pages/protection (placeholders); see docs/ACCEPTANCE_P05.md |
| P06 | Space utilisation | ✅ done | 2026-10-05 | freq x occ on gold + observed occupancy, 7 calc tests, 5 validation SQL, full PBI handoff; B003 pattern weaker-form, D-ENG +285% reported as measured; see projects/p06-space-utilisation/README.md |
| P07 | Asset & maintenance | ☐ | | |
| P08 | Net zero & carbon | ✅ done | 2026-10-05 | scopes/intensity/pathway/baseload on gold marts, 7 calc tests, 4 validation SQL, full PBI handoff; B007 confirmed top (48.8% baseload), B019 default-only; see projects/p08-net-zero-carbon/README.md |
| P09 | Compliance tracker | ☐ | | |
| P10 | Mock institutional return | ☐ | | |
| P11 | IFC → analytics | ☐ | | |
| P12 | COBie validator & loader | ☐ | | |
| P13 | Uniclass mapper | ☐ | | |
| P14 | ISO 19650 checker | ☐ | | |
| P15 | BMS/sensor ingestion | ☐ | | |
| P16 | Energy anomaly detection | ☐ | | |
| P17 | Air quality & occupancy | ☐ | | |
| P18 | Digital twin data layer | ☐ | | |
| P19 | Spatial analysis | ✅ done | 2026-10-05 | OSM footprints + synthetic metrics, area-rank match, 8 buildings, 4 heat clusters, 5/10-min isochrones, outputs: gpkg/geojson/topojson/png/folium/qml/csv + PBI map handoff; see projects/p19-spatial-carbon-map/README.md |
| P20 | Governance & literacy pack | ☐ | | |
