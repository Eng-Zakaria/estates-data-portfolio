"""Lakehouse ingest (P01): bronze → silver with quarantine. Synthetic-data labels retained."""

from .storage import resolve_root

__all__ = ["resolve_root"]
