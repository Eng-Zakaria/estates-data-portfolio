"""P15 point health and fault detection.

Works on a readings frame with columns
`ts, point_id, value, unit, quality` (already validated) plus the point
registry, and produces:

  * `findings`  - one row per detected fault window (rule id from the contract)
  * `health`    - per-point staleness / flat-line / completeness summary

The same rule ids (SEM-01..SEM-04, STALENESS) are used by the Grafana point
health dashboard and the Node-RED alert rows, so a finding here can be traced
back to what an operator would see on screen.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from export_bms_trends import LOCAL_TZ
from validate import load_registry

STALENESS = "STALENESS"
SEM01 = "SEM-01"  # simultaneous heating and cooling
SEM02 = "SEM-02"  # stuck valve
SEM03 = "SEM-03"  # out-of-hours operation
SEM04 = "SEM-04"  # flat-line sensor
SEM05 = "SEM-05"  # sustained sensor drift

# The plant occupancy schedule the SEM-03 rule compares against, in local time.
# A weekend schedule is not a wildcard: teaching weekends and maintenance
# windows run a shorter day, and a fan spinning at 02:00 on a Sunday is still a
# finding, while 11:00 on a Saturday is not.
OUT_OF_HOURS_START = 7
OUT_OF_HOURS_END = 19
WEEKEND_START = 9
WEEKEND_END = 17

# measurement jitter smaller than this is treated as noise, not as movement
NOISE_BAND = 1.0


@dataclass(frozen=True)
class DetectionConfig:
    interval_minutes: int = 5
    staleness_gap_intervals: int = 2  # >= 2 missing intervals = stale
    stuck_min_samples: int = 30
    flatline_min_samples: int = 60  # 6 h at 15 min, 5 h at 5 min
    heat_cool_threshold_pct: float = 20.0
    fan_running_threshold_pct: float = 20.0
    drift_min_rho: float = 0.98  # |Spearman rho| over a window == sustained drift
    # 6 h at a 5-min cadence: long enough that a normal control action (ramp,
    # overshoot, settle) happens and reverses inside one window, while a
    # miscalibrated sensor keeps going
    drift_window_samples: int = 72
    # a healthy control signal also ramps, so the change must clear this floor
    drift_min_delta: float = 25.0
    # and the ramp must not reverse by more than this inside the window
    drift_min_reversal: float = 10.0
    peer_moving_min_range: float = 1.0  # a valve is "moving" if range > 1%


# the shape every caller (and the Grafana queries) expects, declared once so a
# run with no findings still returns the documented columns instead of an
# untyped empty frame
FINDING_COLUMNS = ["rule_id", "point_id", "start_ts", "end_ts", "samples", "detail"]

HEALTH_COLUMNS = [
    "point_id",
    "building",
    "system",
    "point_class",
    "samples",
    "completeness_pct",
    "last_seen",
    "max_gap_minutes",
    "pct_suspect_quality",
    "healthy",
]


def point_classes(registry: dict[str, dict[str, str]]) -> dict[str, str]:
    return {pid: row["point_class"] for pid, row in registry.items()}


def equipment_of(registry: dict[str, dict[str, str]]) -> dict[str, str]:
    """point_id -> equipment key (building.equipment), used to pair valves."""
    return {pid: f"{row['building']}.{row['equipment']}" for pid, row in registry.items()}


def _numeric(readings: pd.DataFrame) -> pd.DataFrame:
    """Coerce timestamps and values, dropping rows that are not usable numbers.

    `value` is forced to object before coercion: assigning a non-numeric string
    into an existing float column raises in pandas 3, and the dead-lettered
    messages that reach this function do carry strings.
    """
    frame = readings.copy()
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True, errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"].astype(object), errors="coerce")
    return frame.dropna(subset=["ts", "value"])


def detect(
    readings: pd.DataFrame, registry_path: str | Path | None = None, config: DetectionConfig | None = None
) -> pd.DataFrame:
    """Return findings rows: rule_id, point_id, start_ts, end_ts, samples, detail."""
    cfg = config or DetectionConfig()
    registry = load_registry(str(registry_path or Path(__file__).resolve().parent / "point_registry.csv"))
    classes = point_classes(registry)
    equips = equipment_of(registry)
    frame = _numeric(readings)
    if frame.empty:
        return pd.DataFrame(columns=FINDING_COLUMNS)

    findings: list[dict[str, object]] = []
    findings.extend(_staleness(frame, classes, cfg))
    findings.extend(_simultaneous(frame, classes, equips, cfg))
    findings.extend(_stuck(frame, classes, equips, cfg))
    findings.extend(_out_of_hours(frame, classes, cfg))
    findings.extend(_drift_and_flatline(frame, classes, cfg))
    # a stuck valve is also a flat-line, so both rules legitimately fire on the
    # same window. Merge them: SEM-02 is the diagnosis (it names the valve and
    # the peer that moved), SEM-04 the symptom, and one row per window keeps
    # the alert queue free of duplicates an engineer has to triage twice.
    findings = _dedupe_symptoms(findings)
    out = pd.DataFrame(findings, columns=FINDING_COLUMNS)
    if out.empty:
        return out
    return out.sort_values(["rule_id", "point_id", "start_ts"]).reset_index(drop=True)


def _ts(value: object) -> pd.Timestamp:
    """Narrow a finding's timestamp field, which is typed as `object` because
    findings carry mixed value types."""
    return pd.Timestamp(value)  # type: ignore[arg-type]


def _dedupe_symptoms(findings: list[dict[str, object]]) -> list[dict[str, object]]:
    """Drop SEM-04 flat-lines fully covered by a SEM-02 stuck-valve finding."""
    stuck = [f for f in findings if f["rule_id"] == SEM02]
    kept: list[dict[str, object]] = []
    for finding in findings:
        if finding["rule_id"] == SEM04:
            covered = any(
                str(f["point_id"]) == str(finding["point_id"])
                and _ts(f["start_ts"]) <= _ts(finding["start_ts"])
                and _ts(f["end_ts"]) >= _ts(finding["end_ts"])
                for f in stuck
            )
            if covered:
                continue
        kept.append(finding)
    return kept


def _staleness(frame: pd.DataFrame, classes: dict[str, str], cfg: DetectionConfig) -> list[dict[str, object]]:
    """A point with a gap larger than the configured interval budget is stale."""
    out: list[dict[str, object]] = []
    gap_limit = pd.Timedelta(minutes=cfg.interval_minutes * (cfg.staleness_gap_intervals + 1))
    for raw_id, grp in frame.groupby("point_id"):
        point_id = str(raw_id)
        grp = grp.sort_values("ts")
        deltas = grp["ts"].diff()
        for idx in grp.index[deltas > gap_limit]:
            prev_ts = grp["ts"].shift().loc[idx]
            out.append(
                {
                    "rule_id": STALENESS,
                    "point_id": point_id,
                    "start_ts": prev_ts,
                    "end_ts": grp["ts"].loc[idx],
                    "samples": int((grp["ts"] > prev_ts).sum()),
                    "detail": f"no valid samples for {(grp['ts'].loc[idx] - prev_ts).total_seconds() / 60:.0f} min "
                    f"({classes.get(point_id, '?')} on {point_id})",
                }
            )
    return out


def _simultaneous(
    frame: pd.DataFrame, classes: dict[str, str], equips: dict[str, str], cfg: DetectionConfig
) -> list[dict[str, object]]:
    """SEM-01: heating and cooling valves both open on the same equipment."""
    valves = frame[frame["point_id"].map(classes).isin(["heating_valve", "cooling_valve"])]
    if valves.empty:
        return []
    piv = valves.assign(cls=valves["point_id"].map(classes), equip=valves["point_id"].map(equips))
    wide = piv.pivot_table(index="ts", columns=["equip", "cls"], values="value", aggfunc="last")
    out: list[dict[str, object]] = []
    # pivot_table gives a MultiIndex column; build the equipment list from the
    # frames rather than unpacking the index, which pandas-stubs types as str
    equip_names = sorted({str(name) for name in valves["point_id"].map(equips).dropna().unique()})
    for equip in equip_names:
        heat, cool = (equip, "heating_valve"), (equip, "cooling_valve")
        if heat not in wide.columns or cool not in wide.columns:
            continue
        both = (wide[heat] > cfg.heat_cool_threshold_pct) & (wide[cool] > cfg.heat_cool_threshold_pct)
        for start, end in _runs(both, cfg):
            out.append(
                {
                    "rule_id": SEM01,
                    "point_id": f"{equip}.heating_valve",
                    "start_ts": start,
                    "end_ts": end,
                    "samples": int(both.loc[start:end].sum()),
                    "detail": f"heating+cooling both > {cfg.heat_cool_threshold_pct:.0f}% on {equip}",
                }
            )
    return out


def _stuck(
    frame: pd.DataFrame, classes: dict[str, str], equips: dict[str, str], cfg: DetectionConfig
) -> list[dict[str, object]]:
    """SEM-02: valve frozen while its paired valve moves."""
    valves = frame[frame["point_id"].map(classes).isin(["heating_valve", "cooling_valve"])]
    if valves.empty:
        return []
    out: list[dict[str, object]] = []
    for raw_id, grp in valves.groupby("point_id"):
        # a groupby key is typed as any scalar the column could hold; the
        # registry column is text, so narrow it once here
        point_id = str(raw_id)
        grp = grp.sort_values("ts")
        equip = equips.get(point_id, point_id)
        point_class = classes[point_id]
        paired_cls = "cooling_valve" if point_class == "heating_valve" else "heating_valve"
        paired = valves[valves["point_id"] == point_id.replace(point_class, paired_cls)]
        if paired.empty:
            continue
        for start, end, n, held in _constant_runs(grp, cfg.stuck_min_samples):
            window = paired[(paired["ts"] >= start) & (paired["ts"] <= end)]
            # the paired valve counts as moving if it spans more than the noise
            # band anywhere inside the window
            moving = (
                not window.empty and float(window["value"].max() - window["value"].min()) > cfg.peer_moving_min_range
            )
            if moving:
                out.append(
                    {
                        "rule_id": SEM02,
                        "point_id": point_id,
                        "start_ts": start,
                        "end_ts": end,
                        "samples": n,
                        "detail": f"valve constant at {held:.0f}% for {n} samples while {paired_cls} moved on {equip}",
                    }
                )
    return out


def _out_of_hours(frame: pd.DataFrame, classes: dict[str, str], cfg: DetectionConfig) -> list[dict[str, object]]:
    """SEM-03: plant running outside its scheduled hours."""
    fans = frame[frame["point_id"].map(classes) == "fan_speed"].copy()
    if fans.empty:
        return []
    local = fans["ts"].dt.tz_convert(LOCAL_TZ)
    weekday = local.dt.weekday < 5
    start = weekday.map({True: OUT_OF_HOURS_START, False: WEEKEND_START})
    end = weekday.map({True: OUT_OF_HOURS_END, False: WEEKEND_END})
    scheduled = (local.dt.hour >= start) & (local.dt.hour < end)
    flag = (fans["value"] > cfg.fan_running_threshold_pct) & ~scheduled
    out: list[dict[str, object]] = []
    fans["flag"] = flag
    for point_id, grp in fans.groupby("point_id"):
        flagged = grp[grp["flag"]]
        if flagged.empty:
            continue
        for start_ts, end_ts in _runs_on(flagged["ts"].sort_values(), cfg):
            window = flagged[flagged["ts"].between(start_ts, end_ts)]
            mean_fan = float(window["value"].mean())
            local_start = start_ts.tz_convert(LOCAL_TZ)
            schedule = (
                f"{OUT_OF_HOURS_START:02d}:00-{OUT_OF_HOURS_END:02d}:00"
                if local_start.weekday() < 5
                else f"{WEEKEND_START:02d}:00-{WEEKEND_END:02d}:00"
            )
            out.append(
                {
                    "rule_id": SEM03,
                    "point_id": point_id,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "samples": int(window["ts"].nunique()),
                    "detail": (
                        f"fan at {mean_fan:.0f}% at {local_start:%a %H:%M} local, outside the {schedule} schedule"
                    ),
                }
            )
    return out


def _drift_and_flatline(frame: pd.DataFrame, classes: dict[str, str], cfg: DetectionConfig) -> list[dict[str, object]]:
    """SEM-04 (flat-line) and SEM-05 (drift).

    Drift is a sensor reading that keeps moving in one direction over hours,
    which is what a failed calibration looks like. A healthy control signal also
    ramps, so monotonicity alone is not enough: the ramp has to be long enough
    to outlast a normal control action and it must not reverse inside the
    window. Keeping the two rules apart matters operationally as well - a stuck
    valve is an equipment fault an engineer can visit, whereas drift is a sensor
    to recalibrate, and the flat-line case needs neither interpretation.
    """
    out: list[dict[str, object]] = []
    skip = {"occupancy", "setpoint"}  # legitimately steppy / constant by design
    for raw_id, grp in frame.groupby("point_id"):
        point_id = str(raw_id)
        if classes.get(point_id) in skip:
            continue
        grp = grp.sort_values("ts")
        for start, end, n, held in _constant_runs(grp, cfg.flatline_min_samples):
            out.append(
                {
                    "rule_id": SEM04,
                    "point_id": point_id,
                    "start_ts": start,
                    "end_ts": end,
                    "samples": n,
                    "detail": f"flat-line: no change for {n} samples (value {held:.1f})",
                }
            )
        for _, chunk in _rolling_windows(grp, cfg.drift_window_samples):
            if len(chunk) < cfg.drift_window_samples:
                continue
            values = chunk["value"].to_numpy()
            rho = _spearman(values, np.arange(len(chunk), dtype=float))
            if pd.isna(rho) or abs(rho) < cfg.drift_min_rho:
                continue
            # a normal control action changes direction inside its own window;
            # drift keeps going, so require no reversal worth mentioning
            if _max_reversal(values) > cfg.drift_min_reversal:
                continue
            span = float(np.ptp(values))
            if span < cfg.drift_min_delta or chunk["value"].nunique() <= 5:
                continue
            rising = values[-1] > values[0]
            out.append(
                {
                    "rule_id": SEM05,
                    "point_id": point_id,
                    "start_ts": chunk["ts"].iloc[0],
                    "end_ts": chunk["ts"].iloc[-1],
                    "samples": len(chunk),
                    "detail": (
                        f"{'rising' if rising else 'falling'} drift over {len(chunk)} samples: "
                        f"spearman rho={rho:.3f}, {values[0]:.0f}->{values[-1]:.0f} "
                        f"(range {span:.0f})"
                    ),
                }
            )
    return out


def _max_reversal(values: np.ndarray) -> float:
    """Largest move against the running extreme, ignoring the noise band.

    A ramping control signal overshoots and comes back; a drifting sensor does
    not. The extreme is only updated once a value clears the noise band, so
    +/-0.4 C sample jitter on an otherwise monotone series does not register as
    a reversal.
    """
    if len(values) < 2:
        return 0.0
    rising = values[-1] >= values[0]
    running = float(values[0])
    worst = 0.0
    for raw in values:
        value = float(raw)
        if rising:
            if running - value > worst:
                worst = running - value
            if value > running + NOISE_BAND:
                running = value
        else:
            if value - running > worst:
                worst = value - running
            if value < running - NOISE_BAND:
                running = value
    return worst


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rank correlation without scipy: rank both series, Pearson on ranks."""
    if len(a) < 3:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy(dtype=float)
    rb = pd.Series(b).rank().to_numpy(dtype=float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def _runs(mask: pd.Series, cfg: DetectionConfig) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Contiguous True runs of a boolean mask over time."""
    return _runs_on(mask.index.to_series()[mask.to_numpy()], cfg)


def _runs_on(index: pd.Series, cfg: DetectionConfig) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Contiguous True runs -> (start, end) timestamps.

    Contiguity is measured against the configured sampling interval, not wall
    time: at a 5-minute cadence every sample is more than a minute after the
    previous one, so a wall-clock rule would report one finding per sample.
    A gap of more than one expected interval ends the run.
    """
    tolerance = pd.Timedelta(minutes=cfg.interval_minutes)
    out: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    start: pd.Timestamp | None = None
    prev: pd.Timestamp | None = None
    for raw_ts in index:
        ts = pd.Timestamp(raw_ts)
        if start is None or prev is None:
            start = prev = ts
        elif ts - prev > tolerance:
            out.append((start, prev))
            start = prev = ts
        else:
            prev = ts
    if start is not None and prev is not None:
        out.append((start, prev))
    return out


def _constant_runs(grp: pd.DataFrame, min_samples: int) -> list[tuple[pd.Timestamp, pd.Timestamp, int, float]]:
    """Constant-value runs of at least min_samples, as (start, end, n, held_value).

    A timestamp gap also ends a run: samples on either side of a dropout were
    never delivered, so they are not evidence of a frozen sensor.
    """
    grp = grp.sort_values("ts")
    changed = grp["value"].ne(grp["value"].shift()) | grp["ts"].diff().gt(pd.Timedelta(minutes=10))
    out: list[tuple[pd.Timestamp, pd.Timestamp, int, float]] = []
    for _, chunk in grp.groupby(changed.cumsum()):
        if len(chunk) >= min_samples:
            out.append((chunk["ts"].iloc[0], chunk["ts"].iloc[-1], len(chunk), float(chunk["value"].iloc[0])))
    return out


def _rolling_windows(grp: pd.DataFrame, window: int) -> Iterator[tuple[int, pd.DataFrame]]:
    """Non-overlapping windows from the top. Non-overlapping on purpose: a
    drift that runs for hours should be reported once, not once per window."""
    for start in range(0, len(grp), window):
        yield start, grp.iloc[start : start + window]


def health_summary(
    readings: pd.DataFrame, registry_path: str | Path | None = None, config: DetectionConfig | None = None
) -> pd.DataFrame:
    """Per-point health: last seen, sample count, gap, expected vs actual completeness."""
    cfg = config or DetectionConfig()
    registry = load_registry(str(registry_path or Path(__file__).resolve().parent / "point_registry.csv"))
    frame = _numeric(readings)
    expected_per_day = 24 * 60 / cfg.interval_minutes
    rows: list[dict[str, object]] = []
    seen = frame.groupby("point_id")["ts"]
    for point_id in sorted(set(registry) | set(frame["point_id"].unique())):
        if point_id in seen.groups:
            grp = frame[frame["point_id"] == point_id].sort_values("ts")
            count = len(grp)
            span_min = (grp["ts"].iloc[-1] - grp["ts"].iloc[0]).total_seconds() / 60
            # inclusive of both endpoints: 12 samples at a 5-min cadence span
            # 55 minutes, which is 12 expected samples, not 11
            expected = max(1.0, span_min / cfg.interval_minutes + 1.0)
            last_seen = grp["ts"].iloc[-1]
            max_gap_min = grp["ts"].diff().dt.total_seconds().max() / 60 if count > 1 else 0.0
            pct_suspect = float((grp["quality"] == "suspect").mean())
        else:
            count, last_seen, max_gap_min, pct_suspect = 0, pd.NaT, float("nan"), 0.0
            expected = expected_per_day
        rows.append(
            {
                "point_id": point_id,
                "building": registry.get(point_id, {}).get("building", ""),
                "system": registry.get(point_id, {}).get("system", ""),
                "point_class": registry.get(point_id, {}).get("point_class", ""),
                "samples": count,
                "completeness_pct": round(100.0 * count / expected, 2) if expected else 0.0,
                "last_seen": last_seen,
                "max_gap_minutes": round(max_gap_min, 1) if count > 1 else None,
                "pct_suspect_quality": round(100.0 * pct_suspect, 2),
                "healthy": bool(
                    count > 0 and (max_gap_min or 0) <= cfg.interval_minutes * (cfg.staleness_gap_intervals + 1)
                ),
            }
        )
    return pd.DataFrame(rows, columns=HEALTH_COLUMNS)
