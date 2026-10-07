"""P14 CLI.

    iso19650-check <folder> --config conventions/uk_national_annex.yml --format text|html|json|junit
                   [--suggest] [--register container_register.csv] [--fail-on error|warning|none]
    iso19650-apply  <folder> --config ... [--dry-run|--apply]   # rename case/separator fixes only
    iso19650-rollback <folder> --log rename_log.csv

Exit code 1 when blocking findings remain (`--fail-on`, default `error`) so the command can gate CI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:  # allow `python projects/p14-iso19650-checker/src/cli.py ...`
    sys.path.insert(0, str(SRC))

DEFAULT_CONFIG = Path("projects/p14-iso19650-checker/conventions/uk_national_annex.yml")
DEFAULT_OUT = Path("data/iso19650/report")

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Convention-agnostic information container (ISO 19650-style) naming checker.",
)


def _load(folder: Path, config: Path, register: Path | None) -> tuple[object, object]:
    from checker import check_folder, load_convention

    convention = load_convention(config)
    result = check_folder(folder, convention, register=register)
    return convention, result


@app.command("check")
def check_cmd(
    folder: Annotated[Path, typer.Argument(help="Folder to check")],
    config: Annotated[Path, typer.Option("--config", "-c", help="Convention config YAML")] = DEFAULT_CONFIG,
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Report format: text, html, json, junit")
    ] = "text",
    out: Annotated[Path, typer.Option(help="Output directory for report artefacts")] = DEFAULT_OUT,
    register: Annotated[
        Path | None, typer.Option(help="Existing container register CSV; files missing from it are orphans")
    ] = None,
    suggest: Annotated[bool, typer.Option(help="List trivially fixable renames (never renames anything)")] = False,
    fail_on: Annotated[str, typer.Option(help="Fail (exit 1) on: error, warning, none")] = "error",
    quiet: Annotated[bool, typer.Option(help="Do not write the text summary to stdout")] = False,
) -> None:
    """Check file and container names against a convention."""
    from checker import compliance_summary, container_register, write_csv
    from reporting import render_html, render_json, render_junit, render_text

    if fail_on not in {"error", "warning", "none"}:
        raise typer.BadParameter("--fail-on must be error, warning or none")

    convention, result = _load(folder, config, register)
    summary = compliance_summary(folder, convention, result)
    renames = result.renames if suggest else []

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "container_register.csv", container_register(folder, convention))
    write_csv(out / "compliance_summary.csv", summary)
    write_csv(out / "suggested_renames.csv", [{"from": o, "to": n} for o, n in result.renames])

    if output_format == "json":
        (out / "issues.json").write_text(render_json(result, summary, renames), encoding="utf-8")
    elif output_format == "junit":
        render_junit(result, out / "junit.xml", fail_on=fail_on)
    elif output_format == "html":
        source = convention.source
        (out / "report.html").write_text(
            render_html(
                result,
                summary,
                renames,
                convention_name=convention.name,
                description=convention.description,
                source=source.url if source else "unknown",
                retrieved=source.retrieved if source else "",
            ),
            encoding="utf-8",
        )
    elif output_format != "text":
        raise typer.BadParameter("--format must be text, html, json or junit")

    if output_format == "text" and not quiet:
        typer.echo(render_text(result, summary, renames))
    typer.echo(f"Artefacts written to {out}")

    blocking = {"error": result.error_count, "warning": result.error_count + result.warning_count}.get(fail_on, 0)
    if blocking:
        raise typer.Exit(code=1)


@app.command("apply")
def apply_cmd(
    folder: Annotated[Path, typer.Argument(help="Folder to check and rename")],
    config: Annotated[Path, typer.Option("--config", "-c")] = DEFAULT_CONFIG,
    log: Annotated[Path, typer.Option(help="Rename log (also the rollback input)")] = Path(
        "data/iso19650/report/rename_log.csv"
    ),
    dry_run: Annotated[bool, typer.Option("--dry-run/--apply", help="Preview (default) or rename")] = True,
) -> None:
    """Rename only the trivially fixable names (case, separator). Reversible via `rollback`."""
    from rename import apply_renames

    convention, result = _load(folder, config, None)
    try:
        log.resolve().relative_to(folder.resolve())
    except ValueError:
        pass
    else:
        typer.echo(
            f"WARNING: the rename log would be written inside {folder}. Keep it outside the checked tree, "
            "otherwise the log itself becomes a naming violation and an orphan on the next run."
        )
    outcome = apply_renames(folder, result.renames, dry_run=dry_run, log_path=log)
    mode = "DRY RUN - nothing renamed" if dry_run else "APPLIED"
    typer.echo(
        f"{mode}: {outcome.renamed} rename(s), {outcome.skipped} skipped. Log: {log}"
        + ("" if dry_run else f"\nRollback with: iso19650-rollback {folder} --log {log}")
    )
    typer.echo(f"Convention: {convention.name}; {len(result.renames)} fixable name(s) found.")


@app.command("rollback")
def rollback_cmd(
    folder: Annotated[Path, typer.Argument(help="Folder the renames were applied in")],
    log: Annotated[Path, typer.Option("--log", help="rename_log.csv written by `apply`")] = Path(
        "data/iso19650/report/rename_log.csv"
    ),
) -> None:
    """Undo the renames in a rename log, verifying the content hash of each file."""
    from rename import rollback

    outcome = rollback(folder, log)
    typer.echo(f"Rolled back {outcome.renamed} rename(s), {outcome.skipped} skipped (log: {log}).")
    for record in outcome.records:
        if record.status != "renamed":
            typer.echo(f"  skipped {record.new_path}: {record.detail}")
    if not outcome.renamed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
