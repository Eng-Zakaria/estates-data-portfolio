# P09 methodology — compliance status logic

> **Synthetic data for portfolio demonstration.** All logic below applies to
> the synthetic dataset only; frequencies are illustrative.

## Status logic (single source of truth)

Priority order (implemented in `src/compliance.py::status_for`):

1. **Failed – remedial open**: `result = 'Fail'` AND open remedial action exists
   (`remedial_opened` set, `remedial_closed` NULL).
2. **No record**: `due_date IS NULL` AND `completed_date IS NULL`.
3. **Completed on time**: `completed_date ≤ due_date` → **Compliant**.
4. **Completed late**: `completed_date > due_date` → **Overdue**.
5. **Not yet completed, past due**: `due_date ≤ as_of` → **Overdue**.
6. **Due within 30 days**: `due_date ≤ as_of + 30 days` → **Due within 30 days**.
7. **Future due**: → **Compliant**.

## Days overdue & overdue bands

- `days_overdue = max(0, as_of - due_date)` when `due_date ≤ as_of`; else 0.
- Bands (for risk score):
  - 0 days → band 0
  - 1–30 → band 1
  - 31–90 → band 2
  - 91–180 → band 3
  - 181+ → band 4

## Risk score

```
risk = criticality (1–5) × overdue_band (1–4) × failure_flag
failure_flag = 2 if result = 'Fail' else 1
```

## Frequency caveat

`dim_inspection_type.frequency_months` values are **illustrative configuration**,
not legal duties. See `docs/frequencies.md` for the list and a reminder to
verify each against current legal duties (e.g. fire alarm servicing,
legionella checks, electrical condition reports, gas safety, lifts) before
any real use.

## Remedial ageing

`ageing_days = (closed_date OR as_of) - opened_date`. Bands:
- ≤ 30 days → green
- 31–90 → amber
- > 90 → red

## Synthetic data note

All inspection records, frequencies, and remedial actions are synthetic.
The weekly digest (`scripts/digest.py`) is a rendering demo; Mailpit
integration is a wiring exercise.