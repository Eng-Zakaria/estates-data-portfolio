"""P12 CLI: validate a COBie workbook; load clean records into staging."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


@app.command("validate")
def validate_cmd(
    workbook: Annotated[Path, typer.Argument(help="COBie workbook path")],
    rules: Annotated[Path, typer.Option(help="COBie rules YAML")] = Path(
        "projects/p12-cobie-validator/rules/cobie.yml"
    ),
    air: Annotated[Path, typer.Option(help="AIR rules YAML")] = Path("projects/p12-cobie-validator/rules/air.yml"),
    out: Annotated[Path, typer.Option(help="Output directory for report")] = Path("data/cobie/report"),
) -> None:
    """Validate a COBie workbook and write HTML + CSV + JSON report."""
    from spec import load_rules
    from validate import issues_to_df, validate_workbook

    cobie_rules = load_rules(rules)
    air_rules = load_rules(air)
    result = validate_workbook(workbook, cobie_rules, air_rules)

    out.mkdir(parents=True, exist_ok=True)
    issues_df = issues_to_df(result.issues)
    if issues_df.empty:
        issues_df = issues_df.reindex(
            columns=["sheet", "row", "column", "rule_id", "severity", "message", "suggested_fix"]
        )
    issues_df.to_csv(out / "issues.csv", index=False)
    issues_df.to_json(out / "issues.json", orient="records", indent=2)

    per_sheet = result.per_sheet()
    html = "<h1>COBie Validation Report (synthetic data)</h1>"
    html += f"<p>Score: {result.score:.1f} (100 - 1.5xblocking - 0.5xwarning, floor 0)</p>"
    html += f"<p>Blocking: {result.blocking_count}, Warning: {result.warning_count}</p>"
    html += "<h2>Per-sheet summary</h2>"
    html += per_sheet.to_html(index=False) if not per_sheet.empty else "<p>No issues.</p>"
    html += "<h2>Issues</h2>"
    html += issues_df.to_html(index=False) if not issues_df.empty else "<p>No issues.</p>"
    (out / "report.html").write_text(html, encoding="utf-8")

    print(f"Score: {result.score:.1f}")
    print(f"Blocking: {result.blocking_count}, Warning: {result.warning_count}")
    print(f"Issues written to {out}")

    if result.has_blocking():
        raise typer.Exit(code=1)


@app.command("load")
def load_cmd(
    workbook: Annotated[Path, typer.Argument(help="COBie workbook path")],
    out: Annotated[Path, typer.Option(help="Handover output dir")] = Path("data/cobie/handover"),
    truth: Annotated[Path, typer.Option(help="Truth assets parquet for serial matching")] = Path(
        "data/truth/assets.parquet"
    ),
    dry_run: Annotated[bool, typer.Option(help="Diff only, write nothing")] = False,
) -> None:
    """Load COBie Type/Component/Space rows into staging with quarantine + audit."""
    from loader import load_workbook_to_staging

    res = load_workbook_to_staging(workbook, out, truth if truth.exists() else None, dry_run=dry_run)
    counts = res["counts"]
    print(
        f"inserted={counts['inserted']} updated={counts['updated']} "
        f"unchanged={counts['unchanged']} rejected={counts['rejected']}"
    )
    if dry_run:
        print(res["diff"])
    else:
        print(f"Handover written to {out}")


if __name__ == "__main__":
    app()
