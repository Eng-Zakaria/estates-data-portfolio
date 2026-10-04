# Storage (local / MinIO / S3)

- Default `STORAGE=local`: lakehouse under `data/lakehouse/{bronze,silver,quarantine}`.
- `STORAGE=minio` with `docker compose up -d minio` (console :9001, API :9000). Set `S3_BUCKET` (default `lakehouse-demo`); layout mirrors local as `s3://<bucket>/bronze|silver|quarantine`.
- `STORAGE=s3` same layout on AWS (requires credentials; Terraform in `infra/terraform/` provisions bucket + Glue + Athena).
- DuckDB reads local Parquet directly; for S3 use `httpfs` + `read_parquet('s3://...')`. Athena dialect notes in `platform/queries/*.sql`.
- Demo credentials in `.env.example` are `DEMO ONLY`.
