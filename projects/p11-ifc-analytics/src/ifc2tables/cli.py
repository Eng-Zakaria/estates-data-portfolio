"""P11 CLI: ifc2tables model.ifc --out data/gold/ifc/"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


@app.command("extract")
def extract_cmd(
    ifc: Annotated[Path, typer.Argument(help="Path to IFC file")],
    out: Annotated[Path, typer.Option(help="Output directory for Parquet tables")] = Path("data/gold/ifc"),
) -> None:
    """Extract analytical tables from an IFC model."""
    from .extract import extract_tables, write_tables

    tables = extract_tables(ifc)
    write_tables(tables, out)


@app.command("qa")
def qa_cmd(
    tables: Annotated[Path, typer.Option(help="Directory with Parquet tables")] = Path("data/gold/ifc"),
    out: Annotated[Path, typer.Option(help="Output directory for QA report")] = Path("data/gold/ifc"),
) -> None:
    """Run model QA report."""
    import pandas as pd

    from .qa_report import qa_report

    dfs = {p.stem: pd.read_parquet(p) for p in tables.glob("*.parquet")}
    qa_report(dfs, out)


@app.command("recon")
def recon_cmd(
    tables: Annotated[Path, typer.Option(help="Directory with Parquet tables")] = Path("data/gold/ifc"),
    out: Annotated[Path, typer.Option(help="Output directory for reconciliation")] = Path("data/gold/ifc"),
) -> None:
    """Reconcile model against space register."""
    import pandas as pd

    from .reconcile import reconcile

    dfs = {p.stem: pd.read_parquet(p) for p in tables.glob("*.parquet")}
    reconcile(dfs, out)


if __name__ == "__main__":
    app()
