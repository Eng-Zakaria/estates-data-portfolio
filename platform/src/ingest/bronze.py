"""Bronze loader: raw file → Parquet (all strings) + audit cols + manifest. Idempotent by sha256."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

AUDIT = ["_ingest_id", "_source_system", "_source_file", "_loaded_at", "_row_number", "_row_hash"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_raw(path: Path, source: str) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        if source == "space_register":
            df = pd.read_excel(path, sheet_name=None, header=2)
            frames = []
            for sheet, d in df.items():
                d = d.copy()
                d["_sheet"] = sheet
                frames.append(d)
            df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
            return df
        return pd.read_excel(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    # Preserve literal "N/A" defect markers (default NA would swallow them);
    # empty fields still become None for null checks.
    df_csv = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df_csv.replace({"": None, "nan": None, "None": None, "NaT": None, "NaN": None})


def load_bronze(
    source: str, file: Path, out_root: Path, ingest_date: str | None = None
) -> tuple[Path, dict[str, object]]:
    """Load one file to bronze. Same sha256 → skipped (status=skipped, same ingest_id)."""
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path = out_root / "bronze_manifest.json"
    manifest: list[dict[str, object]] = []
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = sha256_file(file)
    for existing_entry in manifest:
        if existing_entry.get("source") == source and existing_entry.get("sha256") == digest:
            existing = out_root / str(existing_entry["bronze_path"])
            return existing, {**existing_entry, "status": "skipped"}
    ingest_id = f"{ingest_date or datetime.now(UTC).date().isoformat()}-{digest[:8]}"
    df = _read_raw(file, source)
    df = df.astype(str)
    # blank-row cleanup happens in silver; bronze never alters values (blanks kept as 'nan' strings→ restore None?)
    df = df.replace({"nan": None, "None": None, "NaT": None})
    df["_ingest_id"] = ingest_id
    df["_source_system"] = source
    df["_source_file"] = file.name
    df["_loaded_at"] = datetime.now(UTC).isoformat()
    df["_row_number"] = range(1, len(df) + 1)
    df["_row_hash"] = [
        hashlib.sha256("||".join(map(str, r)).encode()).hexdigest()[:16] for r in df.itertuples(index=False)
    ]
    day = ingest_date or datetime.now(UTC).date().isoformat()
    dest = out_root / source / f"ingest_date={day}" / f"{file.stem}-{digest[:8]}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(dest, index=False)
    new_entry: dict[str, object] = {
        "source": source,
        "file": file.name,
        "sha256": digest,
        "rows": int(len(df)),
        "status": "loaded",
        "ingest_id": ingest_id,
        "bronze_path": str(dest.relative_to(out_root)),
    }
    manifest.append(new_entry)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return dest, new_entry
