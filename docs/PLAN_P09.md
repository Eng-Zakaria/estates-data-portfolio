# PLAN: P09 Statutory compliance tracker

## Goal
Compliance status layer on P04 gold: status logic, risk scoring, monthly
snapshots, weekly digest automation, full Power BI handoff.

## Why P09 now
Next free item (P03/P02 occupied). Dependencies stable: `fct_inspection`,
`dim_inspection_type`, `dim_asset`, `dim_building` all green. Fresh
`projects/p09-compliance-tracker/` tree.

## Key facts (measured 2026-10-05, small profile seed 42)
- 40 inspection records across 8 buildings (B001–B008).
- 5 inspection types with illustrative frequencies (3–60 months).
- Asset criticality 1–5; asset types include Boiler, Fire Alarm Panel, Lift.
- Window: Jan–Mar 2026 + some 2025-due records (Fail/overdue seeds).
- **No remedial action table exists in gold** → will generate a synthetic
  `remedial_actions` table at P09 level (documented as enrichment).

## Tasks
1. `src/compliance.py`: status logic (single function, unit-tested with
   boundary cases: due today, due in 30 days, completed late, failed then
   re-passed); risk score = criticality × overdue_band × failure_flag.
2. `tests/`: hand-checked fixtures for status logic + risk score.
3. `scripts/gen_remedial.py`: synthetic remedial_actions table seeded from
   Fail results (max 2 with >90 day ageing per planted finding).
4. `validation/v01–v05.sql`: RAG matrix, overdue list, next-90 calendar,
   remedial ageing, trend.
5. `scripts/digest.py`: Python + Jinja2 weekly HTML digest (overdue,
   due-soon, remedial ageing) → stdout/Mailpit; golden-file test.
6. `methodology.md`: status rules, risk score maths, frequency caveat
   (docs/frequencies.md link), synthetic data note.
7. `powerbi/`: model.md, queries/*.pq, measures.dax, wireframe.md (5
   pages), theme.json, build-guide.md, README.md.
8. `README.md` (9-section), `SPEC.md`, `make p09-run`, `STATUS.md`,
   `DATA.md` (frequencies.md), commit.

## Risks
- Frequencies are illustrative (not legal duties) — `docs/frequencies.md`
  warns the human to verify before real use.
- Warehouse drift (concurrent session) → read gold at build time.
- Monthly snapshots: small window has <3 months; generate 12 synthetic
  snapshots via date-shift for trend page.

## Open questions
- None blocking. Remedial table generated at P09 level; promote to dbt
  later when platform stabilises.