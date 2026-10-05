# PLAN: P06 Space utilisation

## Goal
Utilisation analytics (frequency × occupancy) on P04 gold + observed
occupancy, with full Power BI handoff. No `.pbix` (protocol).

## Why P06 now
Next free item in recommended order (P03/P02 occupied). Dependencies stable:
space/timetable/occupancy marts unaffected by the in-flight CAFM/meter churn.
Fresh `projects/p06-space-utilisation/` tree — no file overlap.

## Key facts (measured 2026-10-05, small profile seed 42)
- 495 spaces (135 Teaching), 12,026 events (Jan–Mar 2026), 248,877 occ
  readings (~95/sensor/day ≈ 15-min cadence ✓ joinable to event windows).
- 222 negative occ readings (0.09%, 29 sensors) → excluded as invalid,
  documented (DQ territory).
- 64 teaching days in dim_date (matches mart available-hours’t 9h/day basis).
- B003 teaching (30 rooms): mart avg freq 0.556 / occ 0.215 — per-room
  ≥70% & <30% check runs in findings.
- D-ENG holds 14,852 m² (181 spaces) → 247.5 m²/staff-FTE vs ≈64 median
  (+285%, NOT the spec's ≈40%) — metric definition to pin down; report
  honestly, default-profile filters documented either way.

## Tasks
1. `src/utilisation.py`: frequency, occupancy_rate, utilisation,
   no_show_flag (observed max < 1.0, coverage-aware), capacity_mismatch
   (<50%), m2_per_fte, variance_to_median, releasable rooms at target.
2. `tests/`: hand fixtures incl. acceptance case (1 room, 3 events).
3. `validation/v01–v05.sql`: overview KPIs; rooms-to-review; day×hour
   heatmap matrix; dept allocation (truth dept mapping documented as
   P06-level enrichment until dim_space carries dept); event no-show detail.
4. `methodology.md`: SMG-style freq×occ definitions (descriptive, no
   official-compliance claim), 09:00–18:00 Mon–Fri teaching-week window,
   no-show/coverage rules, what-if maths.
5. `powerbi/`: model.md, queries/*.pq, measures.dax (12 spec measures),
   wireframe.md (5 pages), theme.json, build-guide.md + checklist,
   README.md (question→insight→decision), screenshots/.
6. `docs/findings.md`: B003 + D-ENG measured on small (honest numbers);
   exact filters for both pages.
7. `streamlit_app.py` mirror; `README.md` (9-section); `SPEC.md`;
   root `make p06-run`; STATUS.md P06; commit.

## Risks
- Truth dept mapping at P06 level (dim_space lacks dept) — documented,
  promoted later.
- Numbers may drift <1% if space/timetable marts rebuild — findings record
  the validated state; re-run validation after P04 changes.
- Warehouse lock contention (concurrent session) → read_only + retry.

## Open questions
- None blocking. D-ENG +285% vs spec ≈40%: reported as measured; default
  profile may differ (filters provided).
