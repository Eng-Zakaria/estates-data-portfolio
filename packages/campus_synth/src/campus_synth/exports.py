"""Messy source-system exports (raw layer). Truth stays clean; mess lives here."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .defects import inject_defects

CATEGORY_VARIANTS = {
    "Teaching": ["Teaching", "teaching", "TEACH", "Teachig"],
    "Office": ["Office", "office", "OFF"],
    "Laboratory": ["Laboratory", "Lab", "lab", "LABORATORY"],
    "Library": ["Library", "library"],
    "Residential": ["Residential", "Resi", "residential"],
    "Catering": ["Catering", "catering"],
    "Sports": ["Sports", "sports"],
    "Support": ["Support", "support", "SUPP"],
}


def _stamp(out: Path, prefix: str, end: date) -> Path:
    return out / f"{prefix}_{end.strftime('%Y%m%d')}.xlsx"


def export_space_register(
    spaces: pd.DataFrame,
    buildings: pd.DataFrame,
    out: Path,
    rng: np.random.Generator,
    defect_rate: float,
    end: date,
) -> tuple[Path, list[dict[str, str]]]:
    name_by_id = dict(zip(buildings.building_id, buildings.building_name))
    df = spaces.copy()
    df["building_name"] = df.building_id.map(name_by_id)
    # mixed spellings + area text
    df["category_messy"] = df["space_category"].map(lambda c: str(rng.choice(CATEGORY_VARIANTS.get(c, [c]))))
    df["area_text"] = df["nia_m2"].map(lambda a: f"{a} {'sqm' if rng.random() < 0.4 else 'm2'}")
    messy = df[["building_name", "room_code", "category_messy", "area_text", "capacity_seats"]].rename(
        columns={"room_code": "Room", "capacity_seats": "Seats"}
    )
    messy, logs = inject_defects(messy, "space_register", rng, defect_rate, key_col="Room")
    # blank rows
    if len(messy) and defect_rate > 0:
        blanks = pd.DataFrame([{c: None for c in messy.columns}])
        messy = pd.concat([messy, blanks], ignore_index=True)
        logs.append({"table": "space_register", "row_key": "blank", "type": "nulls_in_mandatory"})
    path = _stamp(out, "space_register", end).with_suffix(".xlsx")
    # multi-sheet per campus
    b2campus = dict(zip(buildings.building_id, buildings.campus))
    # map via building_name reverse
    n2id = {v: k for k, v in dict(zip(buildings.building_id, buildings.building_name)).items()}
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for campus in sorted(set(buildings.campus)):
            bids = set(buildings[buildings.campus == campus].building_name)
            sheet = messy[messy.building_name.isin(bids)]
            # merged header rows: write title row then header
            sheet.to_excel(w, sheet_name=campus[:31], startrow=2, index=False)
            ws = w.sheets[campus[:31]]
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(sheet.columns))
            ws.cell(row=1, column=1, value=f"Space Register — {campus} campus (SYNTHETIC)")
            ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(sheet.columns))
            ws.cell(row=2, column=1, value="Extract date: see filename. Areas as recorded by survey.")
    _ = n2id
    _ = b2campus
    return path, logs


def export_cafm(
    work_orders: pd.DataFrame, out: Path, rng: np.random.Generator, defect_rate: float, end: date
) -> tuple[Path, list[dict[str, str]]]:
    df = work_orders.copy()
    # different headers
    df = df.rename(
        columns={
            "wo_id": "WO_Number",
            "asset_id": "AssetRef",
            "raised_ts": "Raised",
            "completed_ts": "Completed",
            "cost_gbp": "Cost",
            "status": "Status",
        }
    )

    # 3 date formats
    def fmt(ts: object) -> object:
        if ts is None or pd.isna(ts):
            return None
        t = pd.Timestamp(ts)
        if pd.isna(t):
            return None
        r = rng.random()
        if r < 0.4:
            return t.strftime("%d/%m/%Y %H:%M")
        if r < 0.7:
            return t.isoformat()
        return t.strftime("%d-%b-%y %H:%M")

    df["Raised"] = df["Raised"].map(fmt)
    df["Completed"] = df["Completed"].map(fmt)
    df["Status"] = df["Status"].map(
        lambda s: {
            "Complete": rng.choice(["Complete", "COMP", "Closed"], p=[0.7, 0.2, 0.1]),
            "Open": rng.choice(["Open", "OPEN", "Outstanding"], p=[0.7, 0.2, 0.1]),
        }.get(s, s)
    )
    df["Cost"] = df["Cost"].map(lambda c: f"£{c:,.2f}" if pd.notna(c) else None)
    df, logs = inject_defects(df, "cafm_workorders", rng, defect_rate, key_col="WO_Number", date_cols=["Raised"])
    # completed before raised for a few (explicit defect type)
    if len(df) and defect_rate > 0:
        k = min(3, len(df))
        for i in rng.choice(len(df), size=k, replace=False):
            df.loc[df.index[int(i)], "Completed"] = df.loc[df.index[int(i)], "Raised"]
            logs.append(
                {
                    "table": "cafm_workorders",
                    "row_key": str(df.loc[df.index[int(i)], "WO_Number"]),
                    "type": "completed_before_raised",
                }
            )
    path = out / f"cafm_workorders_{end.strftime('%Y%m%d')}.csv"
    df.to_csv(path, index=False)
    return path, logs


def export_meters(
    readings: pd.DataFrame,
    meters: pd.DataFrame,
    out: Path,
    rng: np.random.Generator,
    defect_rate: float,
    end: date,
) -> tuple[list[Path], list[dict[str, str]]]:
    logs: list[dict[str, str]] = []
    paths: list[Path] = []
    # local time for exports
    df = readings.copy()
    df["ts_local"] = pd.to_datetime(df["ts_utc"], utc=True).dt.tz_convert("Europe/London")
    df["local_date"] = df["ts_local"].dt.date.astype(str)
    # Supplier A: long format (electricity mains), Supplier B: wide (gas)
    elec = df[df.meter_id.str.contains("-E0")].copy()
    gas = df[df.meter_id.str.contains("-G0")].copy()
    elec["ts_local_str"] = elec["ts_local"].dt.strftime("%d/%m/%Y %H:%M")
    elec_long = elec[["meter_id", "ts_local_str", "value", "unit"]].rename(
        columns={"ts_local_str": "local_time", "value": "kwh"}
    )
    elec_long, l1 = inject_defects(
        elec_long, "meter_hh_supplierA", rng, defect_rate, key_col="meter_id", numeric_cols=["kwh"]
    )
    logs += l1
    # gaps: drop 1% of periods
    if len(elec_long) and defect_rate > 0:
        drop = elec_long.sample(frac=min(0.01, defect_rate), random_state=int(rng.integers(0, 10**6))).index
        elec_long = elec_long.drop(drop)
        logs.append({"table": "meter_hh_supplierA", "row_key": f"dropped:{len(drop)}", "type": "gaps"})
    pa = out / f"meter_hh_supplierA_{end.strftime('%Y%m%d')}.csv"
    elec_long.to_csv(pa, index=False)
    paths.append(pa)
    # Wide format: one row per meter-day, 48 columns
    if len(gas):
        gas["slot"] = gas.groupby(["meter_id", "local_date"]).cumcount()
        wide = gas.pivot_table(index=["meter_id", "local_date"], columns="slot", values="value", aggfunc="first")
        wide.columns = [f"HH{c + 1:02d}" for c in wide.columns]
        wide = wide.reset_index()
        wide, l2 = inject_defects(wide, "meter_hh_supplierB", rng, defect_rate, key_col="meter_id")
        logs += l2
        pb = out / f"meter_hh_supplierB_{end.strftime('%Y%m%d')}.csv"
        wide.to_csv(pb, index=False)
        paths.append(pb)
    # cumulative register sample for one meter (illustrates rollover)
    return paths, logs


def export_bms(
    sensor_readings: pd.DataFrame,
    sensors: pd.DataFrame,
    out: Path,
    rng: np.random.Generator,
    defect_rate: float,
    end: date,
) -> tuple[Path, list[dict[str, str]]]:
    # wide: one column per point (first 20 sensors), ISO with offsets, N/A strings
    sids = sensors.sensor_id.tolist()[:20]
    sub = sensor_readings[sensor_readings.sensor_id.isin(sids)].copy()
    wide = sub.pivot_table(index="ts_utc", columns="sensor_id", values="value", aggfunc="first")
    wide.index = pd.to_datetime(wide.index, utc=True).tz_convert("Europe/London").strftime("%Y-%m-%dT%H:%M:%S%z")
    wide.columns = [
        f"{c} [{'ppm' if i % 3 == 0 else ('count' if i % 3 == 1 else 'C')}]" for i, c in enumerate(wide.columns)
    ]
    wide = wide.reset_index().rename(columns={"ts_utc": "timestamp"})
    # N/A strings (cast to object first to avoid per-cell dtype warnings)
    if len(wide) and defect_rate > 0:
        wide = wide.astype(object)
        for _ in range(min(20, len(wide))):
            wide.iloc[int(rng.integers(0, len(wide))), int(rng.integers(1, wide.shape[1]))] = "N/A"
    path = out / f"bms_trends_{end.strftime('%Y%m%d')}.csv"
    wide.to_csv(path, index=False)
    if defect_rate > 0:
        return path, [{"table": "bms_trends", "row_key": "N/A-strings", "type": "nulls_in_mandatory"}]
    return path, []


def export_inspections(
    inspections: pd.DataFrame, out: Path, rng: np.random.Generator, defect_rate: float, end: date
) -> tuple[Path, list[dict[str, str]]]:
    df = inspections.copy()
    df["result_text"] = df["result"].map(
        lambda r: (
            {
                "Pass": rng.choice(["Pass", "pass - ok", "Satisfactory"]),
                "Fail": rng.choice(["Fail", "FAIL - remedial needed", "unsat"]),
                "Advisory": "Advisory - monitor",
            }.get(r, r)
            if pd.notna(r)
            else r
        )
    )

    # Excel serials for half the dates
    def xldate(d: object) -> object:
        if d is None or (isinstance(d, float) and pd.isna(d)):
            return None
        if rng.random() < 0.5:
            base = date(1899, 12, 30)
            dd = pd.Timestamp(d).date()
            return (dd - base).days
        return str(d)

    df["due_messy"] = df["due_date"].map(xldate)
    df["completed_messy"] = df["completed_date"].map(xldate)
    messy = df[
        [
            "inspection_id",
            "building_id",
            "inspection_type_id",
            "due_messy",
            "completed_messy",
            "result_text",
            "certificate_ref",
        ]
    ]
    messy, logs = inject_defects(messy, "statutory_inspections", rng, defect_rate, key_col="inspection_id")
    path = out / f"statutory_inspections_{end.strftime('%Y%m%d')}.xlsx"
    messy.to_excel(path, index=False)
    return path, logs


def export_timetable(
    timetable: pd.DataFrame, out: Path, rng: np.random.Generator, defect_rate: float, end: date
) -> tuple[Path, list[dict[str, str]]]:
    df = timetable.copy()
    if df.empty:
        path = out / f"timetable_{end.strftime('%Y%m%d')}.csv"
        df.to_csv(path, index=False)
        return path, []
    df["time"] = (
        pd.to_datetime(df["start_ts"], utc=True).dt.tz_convert("Europe/London").dt.strftime("%H:%M")
        + "-"
        + pd.to_datetime(df["end_ts"], utc=True).dt.tz_convert("Europe/London").dt.strftime("%H:%M")
    )
    df["date"] = pd.to_datetime(df["start_ts"], utc=True).dt.tz_convert("Europe/London").dt.date.astype(str)
    df["weeks"] = "1-10,12"  # module-style range (illustrative)
    messy = df[["event_id", "space_id", "date", "time", "weeks", "module_code", "group_size"]]
    messy, logs = inject_defects(messy, "timetable", rng, defect_rate, key_col="event_id")
    path = out / f"timetable_{end.strftime('%Y%m%d')}.csv"
    messy.to_csv(path, index=False)
    return path, logs


def export_sensors(
    sensor_readings: pd.DataFrame,
    out: Path,
    rng: np.random.Generator,
    defect_rate: float,
    end: date,
) -> tuple[Path, list[dict[str, str]]]:
    df = sensor_readings.copy()
    df, logs = inject_defects(df, "sensors", rng, defect_rate * 0.5, key_col="sensor_id", numeric_cols=["value"])
    path = out / f"sensors_{end.strftime('%Y%m%d')}.parquet"
    df.to_parquet(path, index=False)
    return path, logs
