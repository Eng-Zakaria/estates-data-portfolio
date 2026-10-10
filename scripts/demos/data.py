"""Loaders that bind the demo pages to the real marts and project outputs.

Everything here is read-only. If a table or file is missing the loader returns
None and the page builder says so on the page instead of showing invented data.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

# Repo root: ESTATES_REPO wins, otherwise walk up from this file
# (scripts/demos/data.py -> repo root). Never hardcode a machine path here or
# the Linux CI runner silently reads nothing.
REPO = Path(
    os.environ.get("ESTATES_REPO")
    or Path(__file__).resolve().parents[2]
)
GOLD = REPO / "data" / "gold"
P = REPO / "projects"


_WAREHOUSE_CACHE: dict[str, pd.DataFrame | None] = {}


def _from_warehouse(name: str) -> pd.DataFrame | None:
    """Read a mart straight out of the DuckDB warehouse.

    `dbt build` writes to data/warehouse.duckdb, whereas the Parquet extracts in
    data/gold are produced later by the publish/export steps. CI runs only
    `dbt build`, so this fallback is what lets the deployed pages show real
    numbers instead of "not found" notices.
    """
    if name in _WAREHOUSE_CACHE:
        return _WAREHOUSE_CACHE[name]
    db = REPO / "data" / "warehouse.duckdb"
    if not db.exists():
        _WAREHOUSE_CACHE[name] = None
        return None
    try:
        connection = duckdb.connect(str(db), read_only=True)
    except Exception:
        _WAREHOUSE_CACHE[name] = None
        return None
    try:
        found = connection.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'main' AND table_name = ?",
            [name],
        ).fetchone()
        if not found:
            _WAREHOUSE_CACHE[name] = None
            return None
        df = connection.execute(f'SELECT * FROM "{name}"').df()
        _WAREHOUSE_CACHE[name] = df
        return df
    except Exception:
        _WAREHOUSE_CACHE[name] = None
        return None
    finally:
        connection.close()


def gold(name: str) -> pd.DataFrame | None:
    """Prefer the published Parquet extract; fall back to the warehouse."""
    path = GOLD / f"{name}.parquet"
    if path.exists():
        try:
            return pd.read_parquet(path)
        except Exception:
            pass
    return _from_warehouse(name)


def parquet(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def json_file(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def yaml_file(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def con(db: Path) -> duckdb.DuckDBPyConnection | None:
    if not db.exists():
        return None
    try:
        return duckdb.connect(str(db), read_only=True)
    except Exception:
        return None


def query(db: Path, sql: str) -> pd.DataFrame | None:
    connection = con(db)
    if connection is None:
        return None
    try:
        return connection.execute(sql).df()
    except Exception:
        return None
    finally:
        connection.close()


# ---------------------------------------------------------------- foundations


def truth_tables() -> list[dict[str, Any]]:
    truth = REPO / "data" / "truth"
    if not truth.exists():
        return []
    out = []
    for f in sorted(truth.glob("*.parquet")):
        try:
            n = len(pd.read_parquet(f, columns=[]))
        except Exception:
            n = -1
        out.append({"table": f.stem, "rows": n})
    return out


def defect_catalogue() -> tuple[list[str], list[int]] | None:
    doc = yaml_file(REPO / "data" / "raw" / "ground_truth.yaml")
    if not doc:
        return None
    defects = doc.get("defects") or doc.get("defect_log") or []
    if not isinstance(defects, list) or not defects:
        return None
    counts: dict[str, int] = {}
    for d in defects:
        if isinstance(d, dict):
            key = str(d.get("defect_type") or d.get("type") or "unknown")
        else:
            key = str(d)
        counts[key] = counts.get(key, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [k for k, _ in ordered], [v for _, v in ordered]


def reconciliation() -> pd.DataFrame | None:
    doc = json_file(REPO / "data" / "lakehouse" / "reconciliation.json")
    if not doc:
        return None
    return pd.DataFrame(doc)


def quarantine_reasons() -> pd.DataFrame | None:
    """Aggregate _reject_reason across every silver quarantine table."""
    q = REPO / "data" / "lakehouse" / "quarantine"
    if not q.exists():
        return None
    frames = []
    for f in sorted(q.rglob("*.parquet")):
        try:
            df = pd.read_parquet(f)
        except Exception:
            continue
        if "_reject_reason" not in df.columns:
            continue
        df = df.assign(source=f.parent.name)
        frames.append(df[["source", "_reject_reason"]])
    if not frames:
        return None
    allq = pd.concat(frames, ignore_index=True)
    return (
        allq.groupby(["source", "_reject_reason"])
        .size()
        .reset_index(name="rows")
        .sort_values("rows", ascending=False)
    )


def dbt_inventory() -> dict[str, Any] | None:
    """Prefer the compiled manifest; fall back to parsing project files plus live
    warehouse row counts so the page still works before `dbt docs generate`."""
    manifest = json_file(REPO / "platform" / "dbt" / "target" / "manifest.json")
    models: list[dict[str, Any]] = []
    test_count = 0
    contract_count = 0
    source = "manifest.json"
    row_counts: dict[str, int] = {}

    if manifest:
        nodes = manifest.get("nodes", {})
        for node in nodes.values():
            if node.get("resource_type") != "model":
                continue
            documented = sum(
                1
                for c in (node.get("columns") or {}).values()
                if c.get("description") or (c.get("meta") or {}).get("description")
            )
            models.append(
                {
                    "model": node.get("name"),
                    "materialized": (node.get("config") or {}).get("materialized"),
                    "columns": len(node.get("columns") or {}),
                    "documented": documented,
                    "tests": len(node.get("tests") or []),
                    "contract": bool((node.get("contract") or {}).get("enforced")),
                }
            )
        test_count = sum(1 for n in nodes.values() if n.get("resource_type") == "test")
        contract_count = sum(1 for m in models if m["contract"])
        sources_n = len(manifest.get("sources", {}))
        exposures_n = sum(1 for n in nodes.values() if n.get("resource_type") == "exposure")
    else:
        source = "project files + warehouse"
        project = REPO / "platform" / "dbt"
        if not project.exists():
            return None
        described: dict[str, dict[str, Any]] = {}
        tests_by_model: dict[str, int] = {}
        contracts: set[str] = set()
        for yml in sorted(project.rglob("*.yml")):
            doc = yaml_file(yml)
            if not isinstance(doc, dict):
                continue
            entries = doc.get("models") or []
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name")
                if not name:
                    continue
                info = described.setdefault(
                    name, {"columns": 0, "documented": 0, "materialized": None}
                )
                cols = entry.get("columns") or []
                if isinstance(cols, dict):
                    cols = [dict(v or {}, name=k) for k, v in cols.items()]
                if not isinstance(cols, list):
                    cols = []
                cols = [c for c in cols if isinstance(c, dict)]
                info["columns"] += len(cols)
                info["documented"] += sum(
                    1
                    for c in cols
                    if c.get("description") or (c.get("meta") or {}).get("description")
                )
                mat = (entry.get("config") or {}).get("materialized")
                if mat:
                    info["materialized"] = mat
                n_tests = 0
                for c in cols:
                    n_tests += len(c.get("tests") or []) + len(c.get("data_tests") or [])
                n_tests += len(entry.get("tests") or []) + len(entry.get("data_tests") or [])
                tests_by_model[name] = tests_by_model.get(name, 0) + n_tests
                contract = (entry.get("config") or {}).get("contract")
                if isinstance(contract, dict) and contract.get("enforced"):
                    contracts.add(name)
        tests_dir = project / "tests"
        singular = len(list(tests_dir.glob("*.sql"))) if tests_dir.exists() else 0

        warehouse = REPO / "data" / "warehouse.duckdb"
        if warehouse.exists():
            try:
                connection = duckdb.connect(str(warehouse), read_only=True)
                try:
                    rows = connection.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'main'"
                    ).fetchall()
                    for (t,) in rows:
                        row_counts[str(t)] = int(
                            connection.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                        )
                finally:
                    connection.close()
            except Exception:
                pass

        models_dir = project / "models"
        for sql in sorted(models_dir.rglob("*.sql")):
            name = sql.stem
            info = described.get(name, {"columns": 0, "documented": 0, "materialized": None})
            models.append(
                {
                    "model": name,
                    "materialized": info["materialized"]
                    or ("view" if name.startswith("stg_") else "table"),
                    "columns": info["columns"],
                    "documented": info["documented"],
                    "tests": tests_by_model.get(name, 0),
                    "contract": name in contracts,
                }
            )
        test_count = sum(tests_by_model.values()) + singular
        contract_count = len(contracts)
        sources_n = 0
        exposures_n = 0

    snaps = project_snapshots = REPO / "platform" / "dbt" / "snapshots"
    snapshots = len(list(project_snapshots.glob("*.sql"))) if snaps.exists() else 0
    seeds_dir = REPO / "platform" / "dbt" / "seeds"
    seeds = len(list(seeds_dir.glob("*.csv"))) if seeds_dir.exists() else 0
    return {
        "models": models,
        "test_count": test_count,
        "snapshots": snapshots,
        "seeds": seeds,
        "sources": sources_n,
        "exposures": exposures_n,
        "catalog_columns": sum(m["columns"] for m in models),
        "contract_count": contract_count,
        "source": source,
        "row_counts": row_counts,
    }


def workflows() -> list[dict[str, Any]]:
    wf_dir = REPO / ".github" / "workflows"
    if not wf_dir.exists():
        return []
    out = []
    for f in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
        doc = yaml_file(f) or {}
        jobs = doc.get("jobs") or {}
        steps = sum(len(j.get("steps") or []) for j in jobs.values())
        out.append(
            {
                "workflow": f.name,
                "name": doc.get("name", f.stem),
                "jobs": len(jobs),
                "steps": steps,
                "triggers": ", ".join(sorted((doc.get("on") or doc.get(True) or {}).keys()))
                if isinstance(doc.get("on", doc.get(True)), dict)
                else str(doc.get("on", "")),
            }
        )
    return out


def make_targets() -> list[tuple[str, str]] | None:
    mk = REPO / "Makefile"
    if not mk.exists():
        return None
    targets: list[tuple[str, str]] = []
    current: list[str] | None = None
    body: list[str] = []
    for line in mk.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("\t"):
            if current:
                body.append(line.strip())
            continue
        # Any non-recipe line closes the previous target.
        if current:
            targets.append(
                (current[0], " ; ".join(b for b in body if not b.startswith("#"))[:90])
            )
            current = None
            body = []
        if ":" in line and not line.startswith(" ") and not line.startswith("@"):
            head = line.split("#")[0].rstrip(":").strip()
            names = [p for p in head.split() if p]
            if names:
                current = names
                body = []
    if current:
        targets.append((current[0], " ; ".join(b for b in body if not b.startswith("#"))[:90]))
    return targets