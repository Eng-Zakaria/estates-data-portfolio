# PLAN: P01 Campus data warehouse (medallion lakehouse)

## Goal
Ingest small-profile messy exports (`data/raw/`) into bronze (strings + audit) → silver (typed, deduped, UTC) with quarantine. Honest rules apply (synthetic labels retained).

## Tasks
1. Scaffold `platform/ingest/` (contracts, bronze, silver per source, refs, storage, reconcile, cli) + `platform/tests/` + `platform/queries/` + `platform/docs/`
2. Contracts: 7 YAML (space, cafm, meter_A, meter_B, bms, inspections, timetable, sensors) with columns/types/nullability/date candidates
3. Bronze loader: xlsx/csv/parquet → Parquet strings + `_ingest_id/_source_system/_source_file/_loaded_at/_row_number/_row_hash`; `bronze_manifest.json` (sha256, rows, status); idempotency (same sha → skip)
4. Silver: per-source normalise/parse/cast/clean/dedupe → valid + quarantine (`_reject_reason`); meter DST local→UTC, wide→long, cumulative→interval+rollover, gap flags; refs with fuzzy suggestions
5. Reconcile: raw=bronze, silver+quarantine=bronze per source (report JSON + md)
6. Storage: `STORAGE=local` default, `minio` via env + `docker-compose.yml`; DuckDB queries
7. Catalogue `platform/docs/catalogue.md` from contracts; lineage table; Mermaid in README
8. Terraform `infra/terraform/` minimal valid (S3 versioned/SSE/blocked, Glue DB, Athena workgroup+limits, IAM least-priv, Budget alarm) + cost warning
9. Tests: bronze idempotent, silver quarantine, DST 46/50, reconciliation zero-loss, planted invalid-rows → quarantine
10. README per template + `docs/ACCEPTANCE_P01.md`; update STATUS P01

## Risks
- Excel merged headers: read with `header=2` (skip 2 title rows) — verified against exporter.
- Pandas NaT vs None in dates; wide meter pivot columns HH01..; local ambiguous times handled via zoneinfo (DST gap/overlap) — never fabricate.
- `rapidfuzz` may be missing → fallback to `difflib`; note in README.
- Terraform binary may be absent locally → keep TF minimal + `fmt`-clean; CI validates.

## Open questions (non-blocking)
- Gold marts are P04 dbt; P01 documents contract only (`silver` schemas + `docs/gold-contract.md`).
- MinIO/S3 paths use same Parquet layout; Athena dialect notes in queries README.
