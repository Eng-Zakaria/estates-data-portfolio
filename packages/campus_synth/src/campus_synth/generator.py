"""Deterministic synthetic campus truth model + planted findings.

Truth tables are clean (zero orphans). Mess/defects are added only in exports.
All timestamps stored UTC. Local-time handling lives in exports.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd

from .config import ProfileConfig
from .utils import hh_index_utc, ifc_guid, make_rng, start_date_for

UTC = UTC

CAMPUSES = ["North", "South", "City"]
BUILDING_USES = ["Teaching", "Laboratory", "Office", "Library", "Residential", "Sports"]
SPACE_CATS = [
    "Teaching",
    "Office",
    "Laboratory",
    "Library",
    "Residential",
    "Catering",
    "Sports",
    "Support",
]
ASSET_TYPES = [
    "AHU",
    "Boiler",
    "Chiller",
    "Pump",
    "Fan Coil",
    "VAV Box",
    "Lighting",
    "Lift",
    "Fire Alarm Panel",
    "Sprinkler Pump",
    "Generator",
    "UPS",
    "BMS Controller",
    "Radiator",
    "Fume Cupboard",
    "Autoclave",
    "Projector",
    "Access Controller",
]
MANUFACTURERS = ["Acme Air", "Remeha-style Generic", "Generic Pumps Ltd", "NoName Controls"]
TRADES = ["Mechanical", "Electrical", "Fabric", "Controls"]
CONTRACTORS = ["Alpha FM", "Beta Maintenance", "Gamma Services"]
FAULT_CODES = ["F-LEAK", "F-NOISE", "F-TRIP", "F-SENSOR", "F-WORN", "F-CONTROL"]


def _building_names(n: int) -> list[str]:
    anon = [f"Building {chr(65 + i % 26)}{'' if i < 26 else f' {i // 26 + 1}'}" for i in range(n)]
    # sprinkle a few "Science Block N" for realism, deterministic positions
    for i in range(0, n, 7):
        anon[i] = f"Science Block {i // 7 + 1}"
    return anon


def gen_buildings(rng: np.random.Generator, n: int) -> pd.DataFrame:
    names = _building_names(max(n, 40))  # stable names across profiles/seeds
    rows = []
    for i in range(1, n + 1):
        bid = f"B{i:03d}"
        use = BUILDING_USES[int(rng.integers(0, len(BUILDING_USES)))]
        if bid in ("B003", "B005"):
            use = "Teaching"
        if bid == "B007":
            use = "Office"
        if bid == "B012":
            use = "Laboratory"
        if bid == "B019":
            use = "Residential"
        gia = float(rng.uniform(2500, 18000))
        nia = gia * float(rng.uniform(0.6, 0.8))
        rows.append(
            {
                "building_id": bid,
                "building_name": names[i - 1],
                "campus": CAMPUSES[(i - 1) % len(CAMPUSES)],
                "gia_m2": round(gia, 1),
                "nia_m2": round(nia, 1),
                "n_floors": int(rng.integers(2, 7)),
                "year_built": int(rng.integers(1960, 2022)),
                "primary_use": use,
                "heating_fuel": "gas" if rng.random() < 0.7 else "heat",
                "epc_band": str(rng.choice(list("BCDE"))),
                "lat": round(50.72 + rng.normal(0, 0.01), 6),
                "lon": round(-3.53 + rng.normal(0, 0.01), 6),
                "ifc_available": bool(i % 2 == 0 or bid in ("B003", "B005")),
            }
        )
    df = pd.DataFrame(rows)
    # Guarantee B003 has IFC for P11 recon story
    df.loc[df.building_id == "B003", "ifc_available"] = True
    return df.sort_values("building_id").reset_index(drop=True)


def gen_floors(rng: np.random.Generator, buildings: pd.DataFrame) -> pd.DataFrame:
    _ = rng
    rows = []
    for _, b in buildings.iterrows():
        for lvl in range(int(b["n_floors"])):
            code = f"L{lvl:02d}" if lvl >= 0 else f"B{abs(lvl):02d}"
            rows.append(
                {
                    "floor_id": f"F-{b['building_id']}-{code}",
                    "building_id": b["building_id"],
                    "level_code": code,
                    "level_name": f"Level {lvl}",
                }
            )
    return pd.DataFrame(rows)


def gen_departments(rng: np.random.Generator) -> pd.DataFrame:
    _ = rng
    # Fixed departments so D-ENG finding is stable across seeds.
    depts = [
        ("D-ENG", "Engineering", "Science", 60.0, 400.0),
        ("D-PHY", "Physics", "Science", 90.0, 600.0),
        ("D-HUM", "Humanities", "Arts", 120.0, 1500.0),
        ("D-MED", "Medicine", "Health", 150.0, 900.0),
        ("D-BUS", "Business", "Social", 80.0, 1100.0),
        ("D-LAW", "Law", "Social", 70.0, 800.0),
    ]
    return pd.DataFrame(
        [{"department_id": d, "name": n, "faculty": f, "staff_fte": s, "student_fte": st} for d, n, f, s, st in depts]
    )


def gen_spaces(
    rng: np.random.Generator,
    buildings: pd.DataFrame,
    floors: pd.DataFrame,
    departments: pd.DataFrame,
    target: int,
    end_date: date,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    dept_ids = departments["department_id"].tolist()
    # weight D-ENG high so m2/FTE is ~40% above median (planted)
    weights = np.array([3.0 if d == "D-ENG" else 1.0 for d in dept_ids])
    weights /= weights.sum()
    # spaces per building proportional to GIA
    gia = buildings.set_index("building_id")["gia_m2"]
    shares = gia / gia.sum()
    counts = (shares * target).round().astype(int)
    # fix rounding drift
    diff = target - int(counts.sum())
    if diff != 0:
        counts.iloc[0] += diff
    rows = []
    seq = 0
    ifc_mismatch: dict[str, list[str]] = {"area_diff_gt10": [], "missing_from_model": []}
    for _, b in buildings.iterrows():
        bid = b["building_id"]
        fl = floors[floors.building_id == bid].reset_index(drop=True)
        n = max(5, int(counts.loc[bid]))
        for k in range(n):
            seq += 1
            f = fl.iloc[int(rng.integers(0, len(fl)))]
            # B003: mostly teaching
            if bid == "B003" and rng.random() < 0.7:
                cat = "Teaching"
            else:
                cat = str(rng.choice(SPACE_CATS, p=[0.25, 0.25, 0.12, 0.08, 0.12, 0.05, 0.05, 0.08]))
            area = round(float(rng.uniform(15, 180) if cat != "Residential" else rng.uniform(12, 30)), 1)
            cap = int(rng.integers(0, 120)) if cat in ("Teaching", "Library") else int(rng.integers(0, 30))
            if cat == "Teaching" and cap < 10:
                cap = int(rng.integers(20, 80))
            dept = str(rng.choice(dept_ids, p=weights))
            sid = f"S-{bid}-{f['level_code']}-{k + 1:03d}"
            has_guid = rng.random() < 0.6
            rows.append(
                {
                    "space_id": sid,
                    "building_id": bid,
                    "floor_id": f["floor_id"],
                    "room_code": f"{bid}-{f['level_code']}-{k + 1:03d}",
                    "space_category": cat,
                    "space_type": "Lecture Theatre" if (cap >= 80) else ("Seminar" if cat == "Teaching" else cat),
                    "capacity_seats": cap,
                    "nia_m2": area,
                    "department_id": dept,
                    "ifc_guid": ifc_guid(rng) if has_guid else None,
                    "valid_from": date(2020, 1, 1),
                    "valid_to": None,
                }
            )
    df = pd.DataFrame(rows)
    # Planted IFC recon: pick 17 B003 rooms deterministically (first 17 sorted)
    b003 = sorted(df[df.building_id == "B003"]["space_id"].tolist())
    if len(b003) >= 17:
        ifc_mismatch["area_diff_gt10"] = b003[:12]
        ifc_mismatch["missing_from_model"] = b003[12:17]
    # Scale areas so sum NIA per building <= GIA (integrity rule)
    for bid in df["building_id"].unique():
        mask = df.building_id == bid
        tot = df.loc[mask, "nia_m2"].sum()
        gia_v = float(buildings.loc[buildings.building_id == bid, "gia_m2"].iloc[0])
        if tot > gia_v * 0.95:
            df.loc[mask, "nia_m2"] = (df.loc[mask, "nia_m2"] * (gia_v * 0.9 / tot)).round(1)
    _ = end_date
    return df.sort_values("space_id").reset_index(drop=True), ifc_mismatch


def gen_assets(rng: np.random.Generator, buildings: pd.DataFrame, spaces: pd.DataFrame, target: int) -> pd.DataFrame:
    per_b = max(10, target // len(buildings))
    rows = []
    seq = 0
    sp_by_b = {b: spaces[spaces.building_id == b].reset_index(drop=True) for b in buildings.building_id}
    for _, b in buildings.iterrows():
        bid = b["building_id"]
        sps = sp_by_b[bid]
        for _ in range(per_b):
            seq += 1
            sp = sps.iloc[int(rng.integers(0, len(sps)))]
            atype = str(rng.choice(ASSET_TYPES))
            age = int(rng.integers(0, 25))
            install = date(int(2026 - age), int(rng.integers(1, 13)), int(rng.integers(1, 28)))
            cond = "A" if age < 5 else ("B" if age < 12 else ("C" if age < 20 else "D"))
            if rng.random() < 0.08:  # noise
                cond = str(rng.choice(list("ABCD")))
            aid = f"A-{bid}-{seq:06d}"
            rows.append(
                {
                    "asset_id": aid,
                    "building_id": bid,
                    "space_id": sp["space_id"],
                    "asset_type": atype,
                    "description_raw": f"{atype} unit {seq} {sp['room_code']}".lower(),
                    "manufacturer": str(rng.choice(MANUFACTURERS)),
                    "model": f"MDL-{int(rng.integers(100, 999))}",
                    "serial_no": f"SN{seq:07d}",
                    "install_date": install,
                    "expected_life_years": int(rng.integers(10, 26)),
                    "condition_grade": cond,
                    "criticality": int(rng.integers(1, 6)),
                    "replacement_cost_gbp": round(float(rng.lognormal(8.5, 0.9)), 2),
                    "cobie_type": atype,
                    # DEV placeholder only — real Uniclass codes require NBS fetch in P13.
                    "uniclass_code_true": f"DEV_PLACEHOLDER_Pr_{atype[:2].upper()}_{seq % 40:02d}"
                    if seq % 3 == 0
                    else None,
                    "ifc_guid": ifc_guid(rng) if rng.random() < 0.6 else None,
                }
            )
    df = pd.DataFrame(rows)
    # Planted B012 boiler: ensure a boiler exists, old, condition D
    if "B012" in set(buildings.building_id):
        cand = df[(df.building_id == "B012") & (df.asset_type == "Boiler")]
        if cand.empty:
            sp0 = sp_by_b["B012"].iloc[0]
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "asset_id": "A-B012-000999",
                                "building_id": "B012",
                                "space_id": sp0["space_id"],
                                "asset_type": "Boiler",
                                "description_raw": "boiler no 2 plant room",
                                "manufacturer": "Generic Pumps Ltd",
                                "model": "MDL-200",
                                "serial_no": "SN9999999",
                                "install_date": date(2008, 3, 1),
                                "expected_life_years": 20,
                                "condition_grade": "D",
                                "criticality": 5,
                                "replacement_cost_gbp": 45000.0,
                                "cobie_type": "Boiler",
                                "uniclass_code_true": "DEV_PLACEHOLDER_Pr_BO_01",
                                "ifc_guid": ifc_guid(rng),
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
        else:
            idx = cand.index[0]
            df.loc[idx, ["condition_grade", "criticality"]] = ["D", 5]
    return df.sort_values("asset_id").reset_index(drop=True)


def gen_work_orders(
    rng: np.random.Generator,
    assets: pd.DataFrame,
    start: date,
    end: date,
    target: int,
    ppm_drop_quarter: str = "2025-Q4",
) -> pd.DataFrame:
    days = (end - start).days
    # base allocation proportional to age/condition weight
    age = 2026 - pd.to_datetime(assets["install_date"]).dt.year
    cond_w = assets["condition_grade"].map({"A": 0.5, "B": 1.0, "C": 2.0, "D": 3.5}).astype(float)
    w = (1 + age / 10) * cond_w
    w = w / w.sum()
    counts = rng.multinomial(target, w)
    rows = []
    seq = 0
    start_ts = datetime(start.year, start.month, start.day, tzinfo=UTC)
    for ai, c in enumerate(counts):
        if c == 0:
            continue
        a = assets.iloc[ai]
        for _ in range(int(c)):
            seq += 1
            wo_type = str(rng.choice(["PPM", "Reactive", "Statutory", "Project"], p=[0.45, 0.35, 0.1, 0.1]))
            raised = start_ts + timedelta(
                seconds=int(rng.integers(0, max(1, days * 86400))),
            )
            prio = str(rng.choice(["P1", "P2", "P3", "P4"], p=[0.05, 0.25, 0.45, 0.25]))
            sla_days = {"P1": 1, "P2": 7, "P3": 28, "P4": 90}[prio]
            target_ts = raised + timedelta(days=sla_days)
            # PPM completion drop in one quarter: leave many PPM open
            q = f"{raised.year}-Q{(raised.month - 1) // 3 + 1}"
            if wo_type == "PPM" and q == ppm_drop_quarter and rng.random() < 0.45:
                started = None
                completed = None
                status = "Open"
            else:
                delay = float(rng.exponential(3 if wo_type == "Reactive" else 7))
                started = raised + timedelta(days=min(delay, 60))
                done = started + timedelta(hours=float(rng.exponential(8)))
                completed = done if done <= datetime(2026, 4, 1, tzinfo=UTC) else None
                status = "Complete" if completed else "Open"
                if completed and completed > target_ts and rng.random() < 0.3:
                    status = "Complete"
            cost = round(float(rng.lognormal(5.2, 0.9)), 2)
            rows.append(
                {
                    "wo_id": f"WO-{seq:07d}",
                    "asset_id": a["asset_id"],
                    "space_id": a["space_id"],
                    "building_id": a["building_id"],
                    "wo_type": wo_type,
                    "priority": prio,
                    "raised_ts": raised,
                    "target_ts": target_ts,
                    "started_ts": started,
                    "completed_ts": completed,
                    "status": status,
                    "trade": str(rng.choice(TRADES)),
                    "contractor": str(rng.choice(CONTRACTORS)),
                    "labour_hours": round(float(rng.exponential(3)), 1),
                    "cost_gbp": cost,
                    "fault_code": str(rng.choice(FAULT_CODES)),
                    "description": f"{wo_type} {a['asset_type']} {a['asset_id']}",
                }
            )
    df = pd.DataFrame(rows)
    # Planted B012 boiler repeat failures: force >=8 reactive in last 12 months
    b012_boilers = assets[(assets.building_id == "B012") & (assets.asset_type == "Boiler")]
    if not b012_boilers.empty and not df.empty:
        basset = b012_boilers.iloc[0]
        last12 = datetime(2025, 4, 1, tzinfo=UTC)
        mask = (df.asset_id == basset["asset_id"]) & (df.wo_type == "Reactive") & (df.raised_ts >= last12)
        have = int(mask.sum())
        need = max(0, 10 - have)
        for i in range(need):
            seq += 1
            raised = last12 + timedelta(days=int(30 * i + rng.integers(0, 20)))
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "wo_id": f"WO-{seq:07d}",
                                "asset_id": basset["asset_id"],
                                "space_id": basset["space_id"],
                                "building_id": "B012",
                                "wo_type": "Reactive",
                                "priority": "P2",
                                "raised_ts": raised,
                                "target_ts": raised + timedelta(days=7),
                                "started_ts": raised + timedelta(days=1),
                                "completed_ts": raised + timedelta(days=2),
                                "status": "Complete",
                                "trade": "Mechanical",
                                "contractor": "Alpha FM",
                                "labour_hours": 4.0,
                                "cost_gbp": 850.0,
                                "fault_code": "F-CONTROL",
                                "description": "Planted repeat boiler fault (synthetic)",
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
    # completed before raised must not occur in truth (defect only in exports)
    return df.sort_values("raised_ts").reset_index(drop=True)


def gen_inspections(
    rng: np.random.Generator, assets: pd.DataFrame, buildings: pd.DataFrame, end: date
) -> tuple[pd.DataFrame, pd.DataFrame]:
    itypes = pd.DataFrame(
        [
            {
                "inspection_type_id": "INSP-LEG",
                "name": "Legionella control check",
                "frequency_months": 3,
                "applies_to_asset_type": "all buildings",
            },
            {
                "inspection_type_id": "INSP-FIRE",
                "name": "Fire alarm servicing",
                "frequency_months": 6,
                "applies_to_asset_type": "Fire Alarm Panel",
            },
            {
                "inspection_type_id": "INSP-LIFT",
                "name": "Lift thorough examination",
                "frequency_months": 6,
                "applies_to_asset_type": "Lift",
            },
            {
                "inspection_type_id": "INSP-GAS",
                "name": "Gas safety check",
                "frequency_months": 12,
                "applies_to_asset_type": "Boiler",
            },
            {
                "inspection_type_id": "INSP-ELEC",
                "name": "Electrical condition report",
                "frequency_months": 60,
                "applies_to_asset_type": "all buildings",
            },
        ]
    )
    rows = []
    seq = 0
    bids = buildings.building_id.tolist()
    for bid in bids:
        for _, t in itypes.iterrows():
            # one due inspection per building/type near end date
            due = end - timedelta(days=int(rng.integers(0, 200)))
            done_within = due + timedelta(days=int(rng.integers(-5, 20)))
            result = "Pass" if rng.random() < 0.85 else ("Advisory" if rng.random() < 0.5 else "Fail")
            completed = done_within if rng.random() < 0.9 else None
            seq += 1
            rows.append(
                {
                    "inspection_id": f"IN-{seq:06d}",
                    "asset_id": None,
                    "building_id": bid,
                    "inspection_type_id": t["inspection_type_id"],
                    "due_date": due,
                    "completed_date": completed if completed else None,
                    "result": result if completed else None,
                    "remedial_required": bool(result == "Fail" and completed),
                    "certificate_ref": f"CERT-{seq:06d}" if completed else None,
                    "inspector": "Inspector A",
                }
            )
    df = pd.DataFrame(rows)
    # Planted: legionella overdue in 3 buildings (no completion, due >90d ago)
    leg_overdue_bids = ["B002", "B004", "B006"] if "B006" in bids else bids[:3]
    for b in leg_overdue_bids:
        m = (df.building_id == b) & (df.inspection_type_id == "INSP-LEG")
        idx = df[m].index[0]
        df.loc[idx, ["due_date", "completed_date", "result", "remedial_required"]] = [
            end - timedelta(days=120),
            None,
            None,
            False,
        ]
    # 2 failed with remedial open >90 days
    fail_bids = ["B001", "B007"] if "B007" in bids else bids[:2]
    for b in fail_bids:
        m = (df.building_id == b) & (df.inspection_type_id == "INSP-FIRE")
        idx = df[m].index[0]
        df.loc[idx, ["due_date", "completed_date", "result", "remedial_required"]] = [
            end - timedelta(days=150),
            (end - timedelta(days=140)),
            "Fail",
            True,
        ]
    _ = assets
    return itypes, df


def gen_weather(rng: np.random.Generator, start: date, end: date) -> pd.DataFrame:
    idx = hh_index_utc(start, end)
    n = len(idx)
    doy = idx.dayofyear.to_numpy()
    hod = idx.hour.to_numpy() + idx.minute.to_numpy() / 60
    annual = 10 + 8 * np.sin(2 * np.pi * (doy - 105) / 365.25)
    daily = 2.5 * np.sin(2 * np.pi * (hod - 9) / 24)
    temp = annual + daily + rng.normal(0, 1.2, n)
    hdd = np.maximum(0, 15.5 - temp) / 48  # per-HH contribution
    cdd = np.maximum(0, temp - 22) / 48
    return pd.DataFrame(
        {
            "ts_utc": idx,
            "temp_c": np.round(temp, 2),
            "hdd_base15_5": np.round(hdd, 4),
            "cdd": np.round(cdd, 4),
        }
    )


def gen_calendar(start: date, end: date) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    rows = []
    for d in dates:
        m = d.month
        if m in (10, 11, 12):
            term, tw = "Autumn", (d.month - 10) * 4 + d.day // 7 + 1
        elif m in (1, 2, 3):
            term, tw = "Spring", (d.month - 1) * 4 + d.day // 7 + 1
        elif m in (4, 5, 6):
            term, tw = "Summer", (d.month - 4) * 4 + d.day // 7 + 1
        else:
            term, tw = "Holiday", 0
        is_wknd = d.weekday() >= 5
        rows.append(
            {
                "date": d.date(),
                "term": term,
                "teaching_week": 0 if (is_wknd or term == "Holiday") else tw,
                "is_holiday": term == "Holiday",
                "is_weekend": is_wknd,
            }
        )
    return pd.DataFrame(rows)


def gen_meters(rng: np.random.Generator, buildings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, b in buildings.iterrows():
        bid = b["building_id"]
        # main electricity + main gas per building, plus 1-2 subs
        rows.append(
            {
                "meter_id": f"M-{bid}-E01",
                "building_id": bid,
                "utility": "electricity",
                "meter_role": "main",
                "parent_meter_id": None,
                "unit": "kWh",
                "interval": "HH",
                "mpan_mprn_synthetic": f"S-E-{bid}-01",
            }
        )
        rows.append(
            {
                "meter_id": f"M-{bid}-G01",
                "building_id": bid,
                "utility": "gas",
                "meter_role": "main",
                "parent_meter_id": None,
                "unit": "kWh",
                "interval": "HH",
                "mpan_mprn_synthetic": f"S-G-{bid}-01",
            }
        )
        if rng.random() < 0.6:
            rows.append(
                {
                    "meter_id": f"M-{bid}-E02",
                    "building_id": bid,
                    "utility": "electricity",
                    "meter_role": "sub",
                    "parent_meter_id": f"M-{bid}-E01",
                    "unit": "kWh",
                    "interval": "HH",
                    "mpan_mprn_synthetic": f"S-E-{bid}-02",
                }
            )
        if rng.random() < 0.3:
            rows.append(
                {
                    "meter_id": f"M-{bid}-W01",
                    "building_id": bid,
                    "utility": "water",
                    "meter_role": "main",
                    "parent_meter_id": None,
                    "unit": "m3",
                    "interval": "daily",
                    "mpan_mprn_synthetic": f"S-W-{bid}-01",
                }
            )
    df = pd.DataFrame(rows)
    # small profile trims to ~26 meters: keep first buildings' mains
    return df


def gen_meter_readings(
    rng: np.random.Generator,
    meters: pd.DataFrame,
    buildings: pd.DataFrame,
    weather: pd.DataFrame,
    calendar: pd.DataFrame,
    b007_cutoff: datetime,
    b019_summer: tuple[date, date],
) -> pd.DataFrame:
    hh = pd.DatetimeIndex(weather["ts_utc"])
    # teaching/holiday lookup by date
    cal = {str(r["date"]): (r["is_holiday"], r["is_weekend"]) for _, r in calendar.iterrows()}
    buse = dict(zip(buildings.building_id, buildings.primary_use))
    gia_d = dict(zip(buildings.building_id, buildings.gia_m2))
    frames = []
    london = hh.tz_convert("Europe/London")
    hod_lon = london.hour.to_numpy() + london.minute.to_numpy() / 60
    dates_str = london.date.astype(str)
    is_wknd = np.array([cal.get(d, (False, True))[1] for d in dates_str])
    is_hol = np.array([cal.get(d, (False, False))[0] for d in dates_str])
    occupied_factor = np.where(is_wknd | is_hol, 0.25, 1.0)
    day_factor = np.where((hod_lon >= 8) & (hod_lon < 18), 1.0, 0.25)
    temps = weather["temp_c"].to_numpy()
    for _, m in meters.iterrows():
        if m["interval"] != "HH" or m["utility"] not in ("electricity", "gas"):
            continue
        bid = m["building_id"]
        use = buse[bid]
        scale = gia_d[bid] / 8000
        if m["utility"] == "electricity":
            base = 8 * scale * (1.8 if use == "Laboratory" else (1.3 if use == "Library" else 1.0))
            occ = (14 * scale) * occupied_factor * day_factor
            if use == "Residential":  # evening peak
                occ = occ * 0.4 + (10 * scale) * ((hod_lon >= 17) & (hod_lon < 23)).astype(float)
            if use == "Library":  # long hours
                occ = (12 * scale) * np.where((hod_lon >= 8) & (hod_lon < 22), 1.0, 0.2) * np.where(is_hol, 0.5, 1.0)
            vals = base + occ + rng.normal(0, base * 0.08, len(hh))
            vals = np.maximum(vals, base * 0.3)
            # Planted B007 overnight baseload 60% of peak from month 10
            if m["meter_id"] == "M-B007-E01":
                peak = float(np.percentile(vals, 99))
                night = (hod_lon >= 0) & (hod_lon < 5)
                after = hh >= pd.Timestamp(b007_cutoff)
                vals = np.where(night & after, 0.60 * peak + rng.normal(0, peak * 0.02, len(hh)), vals)
            # flatline planted meter handled post-hoc (needs 5-day window); do baseline here
        else:  # gas
            hdd_term = np.maximum(0, 15.5 - temps)
            vals = (2 * scale + 3.2 * scale * hdd_term / 10) * np.where(is_hol, 0.7, 1.0) + rng.normal(0, 0.5, len(hh))
            vals = np.maximum(vals, 0.2)
            if bid == "B019":
                s0, s1 = b019_summer
                in_summer = (london.date >= s0) & (london.date <= s1)
                # control fault: winter-like heating through summer
                vals = np.where(in_summer, 2 * scale + 3.2 * scale * 1.2 + rng.normal(0, 0.3, len(hh)), vals)
        q = np.full(len(hh), "ok", dtype=object)
        frames.append(
            pd.DataFrame(
                {
                    "meter_id": m["meter_id"],
                    "ts_utc": hh,
                    "value": np.round(vals, 3),
                    "unit": m["unit"],
                    "quality_flag": q,
                }
            )
        )
    df = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=["meter_id", "ts_utc", "value", "unit", "quality_flag"])
    )
    # Planted flatline M-B015-E01 for 5 days
    if "M-B015-E01" in set(meters.meter_id):
        flat_start = pd.Timestamp(datetime(2025, 11, 10, tzinfo=UTC))
        flat_end = flat_start + pd.Timedelta(days=5)
        msk = (df.meter_id == "M-B015-E01") & (df.ts_utc >= flat_start) & (df.ts_utc < flat_end)
        if msk.any():
            const = float(df.loc[msk, "value"].iloc[0])
            df.loc[msk, ["value", "quality_flag"]] = [const, "flatline-planted"]
    # daily water meters: lightweight (one row/day)
    return df.sort_values(["meter_id", "ts_utc"]).reset_index(drop=True)


def gen_timetable(
    rng: np.random.Generator,
    spaces: pd.DataFrame,
    calendar: pd.DataFrame,
    start: date,
    end: date,
) -> pd.DataFrame:
    teach = spaces[spaces.space_category == "Teaching"].reset_index(drop=True)
    teach_days = calendar[(~calendar.is_weekend) & (~calendar.is_holiday) & (calendar.teaching_week > 0)]
    rows = []
    seq = 0
    slots = [(9, 11), (11, 13), (14, 16), (16, 18)]
    for _, sp in teach.iterrows():
        cap = int(sp["capacity_seats"]) or 30
        # B003 high booking density
        n_per_day = 3 if sp["building_id"] == "B003" else int(rng.integers(1, 4))
        for _, d in teach_days.iterrows():
            if rng.random() < (0.85 if sp["building_id"] == "B003" else 0.55):
                picks = rng.choice(len(slots), size=min(n_per_day, len(slots)), replace=False)
                for p in picks:
                    s_h, e_h = slots[int(p)]
                    seq += 1
                    if sp["building_id"] == "B003":
                        group = max(3, int(cap * rng.uniform(0.15, 0.30)))
                    else:
                        base = cap * rng.uniform(0.4, 1.05)
                        small = cap * 0.3
                        group = max(2, int(base if rng.random() > 0.12 else small))
                    rows.append(
                        {
                            "event_id": f"EV-{seq:07d}",
                            "space_id": sp["space_id"],
                            "start_ts": datetime(d["date"].year, d["date"].month, d["date"].day, s_h, 0, tzinfo=UTC),
                            "end_ts": datetime(d["date"].year, d["date"].month, d["date"].day, e_h, 0, tzinfo=UTC),
                            "module_code": f"MOD-{int(rng.integers(100, 599))}",
                            "department_id": sp["department_id"],
                            "group_size": group,
                            "booked_capacity_need": cap,
                        }
                    )
                    if seq > 120000:  # safety cap
                        break
                if seq > 120000:
                    break
        if seq > 120000:
            break
    df = pd.DataFrame(
        rows,
        columns=[
            "event_id",
            "space_id",
            "start_ts",
            "end_ts",
            "module_code",
            "department_id",
            "group_size",
            "booked_capacity_need",
        ],
    )
    # small profile subsample: keep every Nth to bound size/time
    return df.sort_values("start_ts").reset_index(drop=True)


def gen_sensors_and_readings(
    rng: np.random.Generator,
    spaces: pd.DataFrame,
    timetable: pd.DataFrame,
    start_sensor: datetime,
    end_sensor: datetime,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # choose rooms: prefer B005 lecture theatre + B003 teaching + random
    teach = spaces[spaces.space_category == "Teaching"]
    b005_big = teach[(teach.building_id == "B005")].sort_values("capacity_seats", ascending=False)
    rooms: list[str] = []
    if not b005_big.empty:
        rooms.append(str(b005_big.iloc[0]["space_id"]))
    b003 = teach[teach.building_id == "B003"]["space_id"].tolist()
    rooms += b003[:20]
    rest = (
        spaces[~spaces.space_id.isin(rooms)].sample(frac=1, random_state=int(rng.integers(0, 10**6))).space_id.tolist()
        if len(spaces) > len(rooms)
        else []
    )
    # n rooms decided by caller; return ordered candidate rooms + shuffled rest.
    return rooms, rest


def _gen_sensor_frames(
    rng: np.random.Generator,
    room_ids: list[str],
    spaces: pd.DataFrame,
    timetable: pd.DataFrame,
    start_sensor: datetime,
    end_sensor: datetime,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    idx15 = pd.date_range(start_sensor, end_sensor, freq="15min", tz="UTC")
    n = len(idx15)
    hod = idx15.hour.to_numpy() + idx15.minute.to_numpy() / 60
    # occupancy truth per room: from timetable where applicable
    sens_rows = []
    read_frames = []
    sn_seq = 0
    # index timetable by space for speed
    tt_by_space: dict[str, list[tuple[datetime, datetime, int]]] = {}
    for _, e in timetable.iterrows():
        tt_by_space.setdefault(str(e["space_id"]), []).append((e["start_ts"], e["end_ts"], int(e["group_size"])))
    for rid in room_ids:
        sn_seq += 1
        co2_id = f"SN-{sn_seq:04d}"
        sn_seq += 1
        occ_id = f"SN-{sn_seq:04d}"
        sn_seq += 1
        tmp_id = f"SN-{sn_seq:04d}"
        for sid, stype in ((co2_id, "co2"), (occ_id, "occupancy_count"), (tmp_id, "temp")):
            sens_rows.append(
                {
                    "sensor_id": sid,
                    "space_id": rid,
                    "sensor_type": stype,
                    "install_date": start_sensor.date(),
                }
            )
        # occupancy timeline
        occ_true = np.zeros(n)
        for s, e, g in tt_by_space.get(rid, []):
            m = (idx15 >= pd.Timestamp(s)) & (idx15 < pd.Timestamp(e))
            occ_true[m] = g
        # 15% no-shows globally already via small groups; force B003 extra zeros
        # sensor noise
        occ_obs = np.maximum(0, occ_true + rng.normal(0, 1.5, n)).round().astype(int)
        # ventilation: B005 worst room poor (slow decay, high steady-state)
        is_b005 = rid == room_ids[0]
        vent = 0.35 if is_b005 else 1.0
        # vectorised first-order response via EWMA (fast; avoids per-step Python loop)
        target = 420.0 + occ_true * (38.0 / vent)
        alpha = 0.12
        co2 = pd.Series(target).ewm(alpha=alpha, adjust=False).mean().to_numpy()
        co2 = co2 + rng.normal(0, 8, n)
        if is_b005:
            co2 = np.maximum(co2, 420)
        temp = 21 + np.minimum(occ_true, 40) * 0.02 + np.sin(2 * np.pi * hod / 24) * 0.5 + rng.normal(0, 0.2, n)
        # drift planted SN-0042: find it if in range
        for sid, vals, unit in (
            (co2_id, co2, "ppm"),
            (occ_id, occ_obs.astype(float), "count"),
            (tmp_id, temp, "C"),
        ):
            v = vals.copy()
            if sid == "SN-0042":
                wk6 = start_sensor + timedelta(weeks=6)
                m = idx15 >= pd.Timestamp(wk6)
                v[m] = v[m] + np.arange(m.sum()) * (0.5 if unit == "ppm" else 0.01)
            # stuck/dropout faults sprinkled
            if rng.random() < 0.3:
                s0 = int(rng.integers(0, max(1, n - 200)))
                v[s0 : s0 + 50] = v[s0]  # stuck
            df = pd.DataFrame({"sensor_id": sid, "ts_utc": idx15, "value": np.round(v, 2)})
            read_frames.append(df)
    sensors = pd.DataFrame(sens_rows)
    readings = (
        pd.concat(read_frames, ignore_index=True)
        if read_frames
        else pd.DataFrame(columns=["sensor_id", "ts_utc", "value"])
    )
    return sensors, readings.sort_values(["sensor_id", "ts_utc"]).reset_index(drop=True)


def generate_all(profile: ProfileConfig) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    """Generate every truth table + planted-findings ground truth dict."""
    rng = make_rng(profile.seed)
    end = profile.end_date
    start = start_date_for(end, profile.n_months)
    buildings = gen_buildings(rng, profile.n_buildings)
    floors = gen_floors(rng, buildings)
    departments = gen_departments(rng)
    spaces, ifc_mismatch = gen_spaces(rng, buildings, floors, departments, profile.target_spaces, end)
    assets = gen_assets(rng, buildings, spaces, profile.target_assets)
    work_orders = gen_work_orders(rng, assets, start, end, profile.target_work_orders)
    inspection_types, inspections = gen_inspections(rng, assets, buildings, end)
    weather = gen_weather(rng, start, end)
    calendar = gen_calendar(start, end)
    meters_all = gen_meters(rng, buildings)
    # small profile: keep fewer meters for speed (still >=2 per building)
    if profile.name == "small":
        keep = []
        for bid in buildings.building_id:
            keep += [f"M-{bid}-E01", f"M-{bid}-G01"]
        meters_all = meters_all[meters_all.meter_id.isin(keep)].reset_index(drop=True)
    b007_cutoff = datetime(2025, 1, 1, tzinfo=UTC) if profile.n_months >= 12 else datetime(2026, 2, 1, tzinfo=UTC)
    b019_summer: tuple[date, date] = (date(2025, 7, 7), date(2025, 8, 10))
    if profile.name == "small":  # summer fault inside small window
        b019_summer = (
            (date(2026, 2, 2), date(2026, 3, 9))
            if "B019" not in set(buildings.building_id)
            else (date(2025, 7, 7), date(2025, 8, 10))
        )
    meter_readings = gen_meter_readings(rng, meters_all, buildings, weather, calendar, b007_cutoff, b019_summer)
    timetable = gen_timetable(rng, spaces, calendar, start, end)
    # sensors: last 3 months, n rooms
    sens_end = datetime(end.year, end.month, end.day, 23, 45, tzinfo=UTC)
    sens_start = sens_end - timedelta(days=90) + timedelta(minutes=15)
    ordered_rooms, rest = gen_sensors_and_readings(rng, spaces, timetable, sens_start, sens_end)
    want = min(profile.n_sensor_rooms, len(spaces))
    room_ids = (ordered_rooms + rest)[:want]
    sensors, sensor_readings = _gen_sensor_frames(rng, room_ids, spaces, timetable, sens_start, sens_end)
    # cost pools + activity splits
    cost_pools = pd.DataFrame(
        [
            {
                "pool_id": f"POOL-{y}-{c}",
                "year": y,
                "cost_type": c,
                "amount_gbp": round(float(rng.uniform(2e5, 1.5e6)), 2),
                "allocation_driver": "NIA x activity",
            }
            for y in sorted({start.year, end.year})
            for c in ["rates", "utilities", "cleaning", "maintenance", "security"]
        ]
    )
    activity_splits = pd.DataFrame(
        [
            {
                "department_id": "D-ENG",
                "teaching_pct": 45.0,
                "research_pct": 45.0,
                "other_pct": 10.0,
            },
            {
                "department_id": "D-PHY",
                "teaching_pct": 40.0,
                "research_pct": 50.0,
                "other_pct": 10.0,
            },
            {
                "department_id": "D-HUM",
                "teaching_pct": 70.0,
                "research_pct": 20.0,
                "other_pct": 10.0,
            },
            {
                "department_id": "D-MED",
                "teaching_pct": 50.0,
                "research_pct": 40.0,
                "other_pct": 10.0,
            },
            {
                "department_id": "D-BUS",
                "teaching_pct": 75.0,
                "research_pct": 10.0,
                "other_pct": 15.0,
            },
            {
                "department_id": "D-LAW",
                "teaching_pct": 75.0,
                "research_pct": 10.0,
                "other_pct": 15.0,
            },
        ]
    )
    tables = {
        "buildings": buildings,
        "floors": floors,
        "departments": departments,
        "spaces": spaces,
        "assets": assets,
        "work_orders": work_orders,
        "inspection_types": inspection_types,
        "inspections": inspections,
        "meters": meters_all,
        "meter_readings_hh": meter_readings,
        "weather": weather,
        "academic_calendar": calendar,
        "timetable_events": timetable,
        "sensors": sensors,
        "sensor_readings": sensor_readings,
        "cost_pools": cost_pools,
        "activity_splits": activity_splits,
    }
    # planted findings registry (fixed IDs/dates; small profile marks missing ones)
    building_ids = set(buildings.building_id)

    def has(bid: str) -> bool:
        return bid in building_ids

    gt: dict[str, object] = {
        "seed": profile.seed,
        "profile": profile.name,
        "window": {"start": str(start), "end": str(end)},
        "planted_findings": {
            "B007_overnight_hvac": {
                "building": "B007",
                "cutoff": b007_cutoff.isoformat(),
                "overnight_share_of_peak": 0.60,
                "applies": has("B007"),
            },
            "B019_summer_heating": {
                "building": "B019",
                "weeks": [str(b019_summer[0]), str(b019_summer[1])],
                "applies": has("B019"),
            },
            "B012_boiler_reactive": {
                "building": "B012",
                "min_reactive_12m": 8,
                "applies": has("B012"),
            },
            "B003_low_occupancy": {
                "building": "B003",
                "booked_ge": 0.70,
                "occupancy_lt": 0.30,
                "applies": has("B003"),
            },
            "D-ENG_space_per_fte": {"department": "D-ENG", "above_median": 0.40, "applies": True},
            "legionella_overdue_3b": {
                "buildings": ["B002", "B004", "B006"],
                "applies": has("B006"),
            },
            "failed_remedial_90d": {"buildings": ["B001", "B007"], "applies": True},
            "B005_co2": {
                "note": "worst B005 lecture theatre CO2 >1500ppm >=20% occupied time",
                "applies": has("B005"),
            },
            "meter_flatline": {
                "meter": "M-B015-E01",
                "days": 5,
                "start": "2025-11-10",
                "applies": has("B015"),
            },
            "sensor_drift": {"sensor": "SN-0042", "from_week": 6, "applies": True},
            "ppm_drop_quarter": {"quarter": "2025-Q4", "applies": profile.n_months >= 12},
            "ifc_recon_B003": {**ifc_mismatch, "applies": has("B003")},
        },
        "defects": [],
    }
    return tables, gt
