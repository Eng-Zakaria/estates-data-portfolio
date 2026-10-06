"""P14 CLI: iso19650-check <folder> --config conventions/uk_example.yml --format html|json|junit"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


@app.command("check")
def check_cmd(
    folder: Annotated[Path, typer.Argument(help="Folder to check")],
    config: Annotated[Path, typer.Option(help="Convention config YAML")] = Path(
        "projects/p14-iso19650-checker/conventions/uk_example.yml"
    ),
    format: Annotated[str, typer.Option(help="Output format: html, json, junit")] = "html",
    out: Annotated[Path, typer.Option(help="Output directory for report")] = Path("data/iso19650/report"),
) -> None:
    """Check file naming against a convention config."""
    from checker import check_folder, load_convention, write_register

    convention = load_convention(config)
    result = check_folder(folder, convention)

    out.mkdir(parents=True, exist_ok=True)
    write_register(folder, out / "container_register.csv")

    # Compliance summary
    total = sum(1 for _ in folder.rglob("*") if _.is_file())
    pct = result.compliance_pct(total)
    print(f"Compliance: {pct:.1f}% ({result.error_count} errors in {total} files)")

    if format == "json":
        import json

        (out / "issues.json").write_text(
            json.dumps(
                [
                    {
                        "path": i.path,
                        "rule_id": i.rule_id,
                        "severity": i.severity,
                        "message": i.message,
                        "suggested_fix": i.suggested_fix,
                    }
                    for i in result.issues
                ],
                indent=2,
            )
        )
    elif format == "junit":
        import xml.etree.ElementTree as ET

        root = ET.Element("testsuites")
        suite = ET.SubElement(root, "testsuite", name="iso19650", tests=str(total), failures=str(len(result.issues)))
        for issue in result.issues:
            case = ET.SubElement(suite, "testcase", classname="iso19650", name=issue.path)
            failure = ET.SubElement(case, "failure", message=issue.message)
            failure.text = issue.rule_id
        ET.ElementTree(root).write(out / "junit.xml", encoding="utf-8", xml_declaration=True)
    else:
        html = f"<h1>ISO 19650 Compliance Report</h1><p>Compliance: {pct:.1f}%</p><p>Errors: {result.error_count}</p><table>"
        for i in result.issues:
            html += f"<tr><td>{i.path}</td><td>{i.rule_id}</td><td>{i.severity}</td><td>{i.message}</td></tr>"
        html += "</table>"
        (out / "report.html").write_text(html, encoding="utf-8")

    print(f"Report written to {out}")
    if result.error_count > 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
