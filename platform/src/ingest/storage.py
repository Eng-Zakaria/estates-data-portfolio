"""Storage abstraction: local default, MinIO/S3 via env (same Parquet layout)."""

from __future__ import annotations

import os
from pathlib import Path


def storage_backend() -> str:
    return os.getenv("STORAGE", "local").lower()


def resolve_root(base: Path) -> Path:
    """Resolve output root. For minio/s3 return a local staging path and document remote prefix.

    Remote layout mirrors local: s3://<bucket>/bronze|silver|quarantine.
    Actual S3 writes require fsspec/s3fs credentials; CI uses local.
    """
    backend = storage_backend()
    if backend in ("minio", "s3"):
        bucket = os.getenv("S3_BUCKET", "lakehouse-demo")
        _ = bucket  # documented prefix s3://<bucket>/...; staging locally under base
    return base


def remote_prefix() -> str:
    bucket = os.getenv("S3_BUCKET", "lakehouse-demo")
    return f"s3://{bucket}"
