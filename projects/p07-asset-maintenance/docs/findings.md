# P07 findings (small profile, seed 42 — synthetic)

## Headline (`v01`)

4,938 WOs; PPM completion **93.0%**; planned:reactive **1.88**;
reactive MTTR **3.17 days**; £1.59M WO cost. SLA met: P1 23.7%,
P2 65.2%, P3 85.1%, P4 97.2%.

## Backlog (`v02`)

327 open WOs, almost all 0–30 days old (avg 6.7d) — expected on a
3-month window with `as_of = window end`. Only 4 jobs aged 31–90.

## Bad actors (`v03` — measured, NOT the planted finding)

Top by reactive_12m (all condition D, risk 4–20):

| rank | asset | building | type | reactive_12m | risk |
|---|---|---|---|---|---|
| 1 | A-B003-000520 | B003 | Autoclave | 8 | 8 |
| 2 | A-B006-000970 | B006 | Pump | 8 | 4 |
| 3 | A-B001-000061 | B001 | Fan Coil | 7 | 20 |
| 4 | A-B003-000387 | B003 | Lift | 7 | 20 |
| 5 | A-B003-000464 | B003 | Pump | 7 | 20 |

**The planted B012 boiler is NOT in this profile.** `dim_building` on
the small profile covers B001–B008 only; B012 appears in the default
profile (see `packages/campus_synth` test_planted.py). Same for the
planted 2025-Q4 PPM drop — the small profile starts 2026-01.
Acceptance item "planted boiler in top 3" is therefore reported as
**not present on small**; on default profile it would rank top
(≥8 reactive jobs, forced by the plant). Do not force it.

## PPM completion trend (`v05` — measured March dip)

Jan 100.0%, Feb 99.7%, **Mar 79.4%** — a real measured completion
dip in the current profile window (893 PPM jobs, 79.4% complete).
This is the honest small-profile analogue of the "one-quarter PPM
drop" narrative and is the filter to use: `wo_type='PPM' AND
month(raised_ts)='2026-03'`.

## Lifecycle (`v04`)

Condition mix: 288 A / 440 B / 485 C / 283 D; 373 assets over expected
life (negative remaining % reported, not clamped). 5-year renewal
forecast 2026–2030: £2.11M total, roughly £420k/yr declining
slightly. Cost per m² of GIA ~£0.025/£ (artefact: 3-month cost
window vs whole-asset GIA — noted, not "fixed").

## Repeat failures

169 assets flagged `is_repeat_failure` (≥3 reactive in 12m); top
clusters: B007 Fan Coil 38, B004 AHU 31, B001 BMS Controller 31,
B007 Boiler 26 — the boiler story exists but dispersed; the
single-asset B012 plant is default-only.
