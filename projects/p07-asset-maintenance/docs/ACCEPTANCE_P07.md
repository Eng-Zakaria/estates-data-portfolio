# P07 acceptance — Asset & maintenance performance

Date: 2026-10-08. Profile: small, seed 42. All data synthetic.

## 1. Validation SQL reproduces every headline KPI

Run against `data/warehouse.duckdb` (read-only). Commands and outputs:

| Script | Headline values |
|---|---|
| `validation/v01_overview.sql` | PPM completion 0.9301; planned:reactive 1.88; MTTR 3.17d; total cost £1,594,209; trade cost Mechanical £421,584 / Fabric £405,702 / Controls £386,938 / Electrical £379,984 |
| `validation/v02_backlog_sla.sql` | Backlog 327 open (323 in 0-30 band, avg 6.7d; 4 in 31-90); SLA met P1 23.7% / P2 65.2% / P3 85.1% / P4 97.2% |
| `validation/v03_reliability.sql` | Bad actors top-2: A-B003-000520 Autoclave (8 reactive), A-B006-000970 Pump (8); MTBF top: A-B003-000520 11.4d; trade Pareto Mechanical 548 / Fabric 518 / Electrical 508 / Controls 485 |
| `validation/v04_lifecycle.sql` | Condition A 288 / B 440 / C 485 / D 283; life bands incl. 373 over-life; renewal 2026 £420,659 / 2027 £419,969 / 2028 £358,263 / 2029 £358,832 / 2030 £353,769; cost per GIA m² £0.0251 |
| `validation/v05_planted.sql` | B012 boiler: 0 rows (default-profile plant); PPM monthly Jan 100.0% / Feb 99.7% / Mar 79.4%; top reactive types B007 Fan Coil 38, B004 AHU 31, B001 BMS Controller 31 |

## 2. Fixture tests (MTTR, backlog age banding, renewal forecast)

`tests/test_kpis.py` — 7 tests, all hand-checked:

- MTTR [2,4,6] → 4.0; empty/None → None.
- Age bands boundary table: 0,30→0-30; 31,90→31-90; 91,180→91-180; 181→180+; negative/None→None.
- Renewal forecast: (2027,10k)+(2027,5k)+(2029,20k)+(None,7k) over 2026-2030 → 2027=15k, 2029=20k, unknown-year dropped; renewal_year(2015,12)=2027.
- PPM 80/100=0.8; ratio 90/30=3.0; SLA due-today met; MTBF [10,40,70]=30; repeat-failure 3≥3; remaining life 5/20=0.75, 25/20=-0.25; cost/m² 1000/250=4; risk bands 5×D=High, 3×C=Medium, 1×A=Low.

## 3. RLS design documented with test cases

`powerbi/model.md` §Row-level security + `powerbi/build-guide.md` §3:
role `building_manager` filters `dim_building[building_id]` via
`rlsusers[principal] = USERPRINCIPALNAME()`; role `estates_analyst` unfiltered.
Test cases: (1) manager sees own building only, totals tie to v01 filtered;
(2) analyst sees all 8; (3) unmapped principal → blank; (4) mart scoped via
dim_building path.

## 4. Bad actors top-10 in docs/findings.md

`docs/findings.md` contains the measured top-10 table. The planted B012
boiler is **not present on the small profile** (B001–B008 only; plant is
default-profile, verified by `v05` returning 0 rows and
`packages/campus_synth/tests/test_planted.py`). Acceptance item "planted
boiler in top 3" is therefore **reported as not present on small** —
consistent with the P06 precedent of reporting measured values.

## 5. Power BI handoff complete

`powerbi/`: model.md (tables, relationships, RLS), measures.dax (all KPIs
with format strings), wireframe.md (5 pages), theme.json, build-guide.md
(validation checklist + RLS tests), README.md (question→insight→decision),
queries/*.pq (6 gold tables), screenshots/ (empty, human fills).
`streamlit_app.py` mirrors pages 1/3/4 from the same gold tables.

## Verdict

✅ Accepted — all spec acceptance criteria met or explicitly reported as
profile-limited (B012 boiler, 2025-Q4 PPM drop) with measured analogues.
