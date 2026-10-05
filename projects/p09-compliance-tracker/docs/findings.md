# P09 findings (small profile, seed 42 — synthetic)

## Planted finding 1: legionella-type overdue in 3 buildings — CONFIRMED

`validation/v01_rag_matrix.sql` (RAG matrix) filtered to `inspection_name = 'Legionella control check'` and `rag = 'RED'` shows **3 buildings** (B001, B004, B008) with overdue legionella checks. RAG = RED because `days_overdue > 0` and `status = 'Overdue'`. Exact filter in Page 1: type = "Legionella control check", RAG = Red.

## Planted finding 2: 2 failed inspections with remedial > 90 days — CONFIRMED

`validation/v04_remedial_ageing.sql` ordered by `ageing_days DESC` shows two remedial actions with `ageing_days > 90` (both 120+ days, seeded in `scripts/gen_remedial.py` for the first two Fail rows). Both appear at the top of Page 4 table with red ageing band. Exact filter: `ageing_days > 90`.

## Status logic boundary verification

All 11 unit tests pass (`pytest projects/p09-compliance-tracker/tests/ -v`):
- due today → Overdue
- due in 30 days → Due within 30 days
- due in 31 days → Compliant
- completed on due date → Compliant
- completed after due date → Overdue
- failed with open remedial → Failed – remedial open
- failed closed remedial (re-passed) → Overdue (completed late)
- no due date, no completed → No record
- overdue bands: 0/1-30/31-90/91-180/181+
- risk score maths (criticality × band × failure_flag)
- remedial ageing open vs closed

## Digest golden-file test

```bash
python scripts/digest.py --as-of 2026-03-31 > /tmp/digest.html
diff /tmp/digest.html tests/golden/digest_2026-03-31.html  # passes
```

Golden file committed at `tests/golden/digest_2026-03-31.html`.