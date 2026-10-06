"""P12 CLI: cobie-validate model.xlsx --rules rules/cobie.yml --air rules/air.yml"""

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
    """Validate a COBie workbook and write a report."""
    from spec import load_rules
    from validate import issues_to_df, validate_workbook

    cobie_rules = load_rules(rules)
    air_rules = load_rules(air)
    result = validate_workbook(workbook, cobie_rules, air_rules)

    out.mkdir(parents=True, exist_ok=True)
    issues_df = issues_to_df(result.issues)
    issues_df.to_csv(out / "issues.csv", index=False)
    issues_df.to_json(out / "issues.json", orient="records", indent=2)

    # HTML report
    html = f"<h1>COBie Validation Report</h1><p>Score: {result.score:.1f}</p>"
    html += f"<p>Blocking: {result.blocking_count}, Warning: {result.warning_count}</p>"
    html += issues_df.to_html(index=False)
    (out / "report.html").write_text(html, encoding="utf-8")

    print(f"Score: {result.score:.1f}")
    print(f"Blocking: {result.blocking_count}, Warning: {result.warning_count}")
    print(f"Issues written to {out}")

    if result.has_blocking():
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
