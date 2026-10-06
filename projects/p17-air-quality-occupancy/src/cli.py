"""P17 CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from . import (
    compute_ventilation_metrics,
    compute_ventilation_risk_score,
    compute_thermal_comfort,
    compute_comfort_risk_score,
    compute_occupancy_analysis,
    compute_occupancy_utilization_score,
    compute_sensor_health,
    compute_room_archetypes,
    compute_observed_occupancy_fact,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def ventilation(
    truth_dir: Path = typer.Option(Path("data/truth"), help="Foundation truth parquet dir"),
    output: Path = typer.Option(Path("data/p17_output/ventilation_metrics.parquet"), help="Output file"),
    co2_low: int = typer.Option(1000, help="CO2 low threshold (ppm)"),
    co2_high: int = typer.Option(1500, help="CO2 high threshold (ppm)"),
) -> None:
    """Compute ventilation adequacy metrics from CO2 sensors."""
    df = compute_ventilation_metrics(
        truth_dir=truth_dir,
        co2_threshold_low=co2_low,
        co2_threshold_high=co2_high,
    )
    if df.empty:
        typer.echo("No CO2 sensors found")
        raise typer.Exit(1)
    df = compute_ventilation_risk_score(df)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    typer.echo(f"Ventilation metrics for {len(df)} rooms -> {output}")


@app.command()
def comfort(
    truth_dir: Path = typer.Option(Path("data/truth"), help="Foundation truth parquet dir"),
    output: Path = typer.Option(Path("data/p17_output/thermal_comfort.parquet"), help="Output file"),
    min_temp: float = typer.Option(18.0, help="Comfort min temp (°C)"),
    max_temp: float = typer.Option(24.0, help="Comfort max temp (°C)"),
    overheat: float = typer.Option(26.0, help="Overheating threshold (°C)"),
) -> None:
    """Compute thermal comfort metrics from temperature sensors."""
    df = compute_thermal_comfort(
        truth_dir=truth_dir,
        comfort_min_c=min_temp,
        comfort_max_c=max_temp,
        overheating_c=overheat,
    )
    if df.empty:
        typer.echo("No temperature sensors found")
        raise typer.Exit(1)
    df = compute_comfort_risk_score(df)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    typer.echo(f"Thermal comfort metrics for {len(df)} rooms -> {output}")


@app.command()
def occupancy(
    truth_dir: Path = typer.Option(Path("data/truth"), help="Foundation truth parquet dir"),
    output: Path = typer.Option(Path("data/p17_output/occupancy_analysis.parquet"), help="Output file"),
    no_show_min: int = typer.Option(10, help="No-show threshold (minutes)"),
    overcap_tol: float = typer.Option(1.0, help="Overcapacity tolerance (1.0 = 100%)"),
) -> None:
    """Compute actual vs timetabled occupancy analysis."""
    df = compute_occupancy_analysis(
        truth_dir=truth_dir,
        no_show_threshold_min=no_show_min,
        overcapacity_tolerance=overcap_tol,
    )
    if df.empty:
        typer.echo("No occupancy sensors found")
        raise typer.Exit(1)
    df = compute_occupancy_utilization_score(df)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    typer.echo(f"Occupancy analysis for {len(df)} rooms -> {output}")


@app.command()
def sensor_health(
    truth_dir: Path = typer.Option(Path("data/truth"), help="Foundation truth parquet dir"),
    output: Path = typer.Option(Path("data/p17_output/sensor_health.parquet"), help="Output file"),
    sensor_type: str = typer.Option(None, help="Filter by sensor type (co2, temp, occupancy_count)"),
) -> None:
    """Compute sensor health metrics (stuck, dropouts, drift)."""
    types = [sensor_type] if sensor_type else None
    df = compute_sensor_health(truth_dir=truth_dir, sensor_types=types)
    if df.empty:
        typer.echo("No sensors found")
        raise typer.Exit(1)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    typer.echo(f"Sensor health for {len(df)} sensors -> {output}")


@app.command()
def archetypes(
    truth_dir: Path = typer.Option(Path("data/truth"), help="Foundation truth parquet dir"),
    output: Path = typer.Option(Path("data/p17_output/room_archetypes.parquet"), help="Output file"),
    n_clusters: int = typer.Option(5, help="Number of k-means clusters"),
) -> None:
    """Cluster rooms into archetypes based on usage/environmental profiles."""
    df = compute_room_archetypes(truth_dir=truth_dir, n_clusters=n_clusters)
    if df.empty:
        typer.echo("Not enough data for clustering")
        raise typer.Exit(1)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    typer.echo(f"Room archetypes for {len(df)} rooms -> {output}")


@app.command()
def observed_occupancy(
    truth_dir: Path = typer.Option(Path("data/truth"), help="Foundation truth parquet dir"),
    output: Path = typer.Option(Path("data/p17_output/fct_space_observed_occupancy.parquet"), help="Output file"),
) -> None:
    """Generate fct_space_observed_occupancy fact table for P06 integration."""
    df = compute_observed_occupancy_fact(truth_dir=truth_dir)
    if df.empty:
        typer.echo("No observed occupancy data")
        raise typer.Exit(1)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    typer.echo(f"Observed occupancy fact table ({len(df)} rows) -> {output}")


@app.command()
def all(
    truth_dir: Path = typer.Option(Path("data/truth"), help="Foundation truth parquet dir"),
    output_dir: Path = typer.Option(Path("data/p17_output"), help="Output directory"),
) -> None:
    """Run all P17 analyses and write outputs to directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo("Running ventilation analysis...")
    vent = compute_ventilation_metrics(truth_dir=truth_dir)
    vent = compute_ventilation_risk_score(vent)
    vent.to_parquet(output_dir / "ventilation_metrics.parquet", index=False)
    typer.echo(f"  -> {len(vent)} rooms")

    typer.echo("Running thermal comfort...")
    comfort = compute_thermal_comfort(truth_dir=truth_dir)
    comfort = compute_comfort_risk_score(comfort)
    comfort.to_parquet(output_dir / "thermal_comfort.parquet", index=False)
    typer.echo(f"  -> {len(comfort)} rooms")

    typer.echo("Running occupancy analysis...")
    occ = compute_occupancy_analysis(truth_dir=truth_dir)
    occ = compute_occupancy_utilization_score(occ)
    occ.to_parquet(output_dir / "occupancy_analysis.parquet", index=False)
    typer.echo(f"  -> {len(occ)} rooms")

    typer.echo("Running sensor health...")
    health = compute_sensor_health(truth_dir=truth_dir)
    health.to_parquet(output_dir / "sensor_health.parquet", index=False)
    typer.echo(f"  -> {len(health)} sensors")

    typer.echo("Running room archetypes...")
    arch = compute_room_archetypes(truth_dir=truth_dir)
    arch.to_parquet(output_dir / "room_archetypes.parquet", index=False)
    typer.echo(f"  -> {len(arch)} rooms")

    typer.echo("Generating observed occupancy fact...")
    fact = compute_observed_occupancy_fact(truth_dir=truth_dir)
    fact.to_parquet(output_dir / "fct_space_observed_occupancy.parquet", index=False)
    typer.echo(f"  -> {len(fact)} rows")

    typer.echo(f"\nAll outputs written to {output_dir}")


if __name__ == "__main__":
    app()