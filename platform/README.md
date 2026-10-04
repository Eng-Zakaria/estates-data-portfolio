# P01 Campus data warehouse (medallion lakehouse)

> **Synthetic data for portfolio demonstration. No real building performance or compliance status is implied.**

## 1. Problem statement

Estates data arrives as five-plus messy extracts (space register, CAFM, meters, BMS, inspections, timetable, sensors) with different names, date formats, and local-time quirks. Managers need one typed, deduplicated, queryable layer with bad rows quarantined — not silently dropped — so downstream dashboards (P06–P10) and dbt marts (P04) can trust row counts.

## 2. Architecture

```mermaid
flowchart LR
  RAW[data/raw/*<br/>xlsx/csv/parquet, local time] --> BRONZE[bronze/*.parquet<br/>all strings + audit]
  BRONZE --> SILVER[silver/*.parquet<br/>typed, UTC, deduped]
  BRONZE --> QUAR[quarantine/*.parquet<br/>_reject_reason]
  REFS[refs/*.csv + truth/buildings] --> SILVER
  SILVER --> DUCK[DuckDB queries]
  SILVER --> P04[gold marts (P04 dbt)]
  S3[(S3/MinIO mirror)] -.-> BRONZE
```

Lineage (source file → bronze → silver):

| raw file | bronze table | silver table |
|---|---|---|
| space_register_*.xlsx | bronze/space_register | silver/space_register/silver.parquet |
| cafm_workorders_*.csv | bronze/cafm_workorders | silver/cafm_workorders/silver.parquet |
| meter_hh_supplierA_*.csv | bronze/meter_hh_supplierA | silver/meter_hh_supplierA/silver.parquet |
| meter_hh_supplierB_*.csv | bronze/meter_hh_supplierB | silver/meter_hh_supplierB/silver.parquet |
| bms_trends_*.csv | bronze/bms_trends | silver/bms_trends/silver.parquet |
| statutory_inspections_*.xlsx | bronze/statutory_inspections | silver/statutory_inspections/silver.parquet |
| timetable_*.csv | bronze/timetable | silver/timetable/silver.parquet |
| sensors_*.parquet | bronze/sensors | silver/sensors/silver.parquet |

## 3. Data: sources, licences, synthetic note

All inputs are synthetic `campus_synth` small-profile exports (see root `DATA.md`: no external rows). Truth Parquet in `data/truth/` is used only for the building crosswalk and evaluation. Every chart/query footer must retain the synthetic label.

## 4. Quick start (max 3 commands)

```bash
pip install -e ".[dev]"
make data PROFILE=small
make ingest
```

Direct:

```bash
python -m ingest.cli run-all --raw data/raw --out data/lakehouse --truth data/truth
python -m ingest.cli reconcile --raw data/raw --out data/lakehouse
python -m ingest.cli catalogue --out platform/docs/catalogue.md
```

MinIO (optional): `docker compose up -d minio`, then `STORAGE=minio S3_BUCKET=lakehouse-demo python -m ingest.cli run-all ...` (same layout under `s3://<bucket>/`).

## 5. Results

Small profile, seed 42 (see `docs/ACCEPTANCE_P01.md` for full numbers):

- `make ingest` < 2 min (bronze + silver + reconcile).
- Reconciliation: raw = bronze; silver + quarantine = bronze per source (zero unexplained loss).
- Idempotent re-run: second `run-all` reports `skipped`, row counts unchanged.
- DST: 2026-03-29 yields 46 unique UTC periods per meter; autumn 50-period logic covered by unit test + gaps report.
- Quarantine captures nulls, bad dates, future dates, negatives, unmapped categories/buildings, orphans, duplicates, completed≤raised.
- Queries in `platform/queries/*.sql` run on DuckDB; Athena notes inline.

## 6. Design decisions and trade-offs

- **Bronze never alters values** (all strings + `_ingest_id/_source_system/_source_file/_loaded_at/_row_number/_row_hash`, partitioned `source/ingest_date=...`). Space register multi-sheet read with `header=2` (two merged title rows).
- **Explicit date candidates** (`dates.py`) with format logging; Excel serials via 1899-12-30 base; ambiguous/nonexistent London times → NaT → quarantine (never guess).
- **Meters**: long + wide→long reshape; cumulative→interval with rollover detection; gap report (expected 48/46/50 vs actual) flags only.
- **Refs**: `space_category_map.csv`, `asset_type_map.csv`, dynamic building crosswalk from truth + rapidfuzz suggestions (≥60) in `unmapped_values` report. Trade-off: crosswalk needs truth at ingest; in production this would be a master-data table.
- **Storage**: `STORAGE=local|minio|s3`; remote mirrors local Parquet layout; CI uses local. See `platform/docs/storage.md`.
- Gold contract documented in `platform/docs/gold-contract.md` for P04 (dims/facts names + grain).

## 7. Data quality and testing approach

- `platform/tests/`: bronze idempotency, silver quarantine reasons, DST periods, cumulative rollover, reconciliation zero-loss, planted invalid-rows → quarantine.
- Contracts (`platform/contracts/*.yml`) drive catalogue (`platform/docs/catalogue.md`) and validation.
- `reconciliation.json` written per run; `make ci` fails on unexplained loss.

## 8. Limitations and next steps with real data

- Cumulative-meter path is implemented + tested but not exercised by current synthetic exports (all interval); wd keep for supplier variation.
- Water meters (`daily`) and heat not yet silverised (electricity/gas HH only); add in P04 if needed.
- Real deployment needs S3/Glue/Athena wiring (Terraform provided, not applied), schema-drift alerts (P02), and DQ gates (P03).
- AWS path: see `infra/terraform/` + cost warning below. CI runs `terraform fmt/validate` only.

**Cost warning (AWS, optional):** applying Terraform creates S3 + Glue + Athena + IAM + Budget resources that can incur charges (Athena per-TB-scanned, S3 storage). Default workgroup caps scans at 10 GB/query and a $20/month budget alarm is included, but do not `make aws-apply` without checking region/costs. CI never applies.

## 9. Skills demonstrated

E2 (heterogeneous ingestion + idempotency), E3 (typed modelling + DST/cumulative logic), E4 (contracts, lineage, catalogue, storage abstraction), D1 (reconciliation), D5 (reproducible CI + docs).
