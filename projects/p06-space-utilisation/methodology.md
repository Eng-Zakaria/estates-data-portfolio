# P06 methodology — space utilisation definitions

> **Synthetic data for portfolio demonstration.** Definitions below are
> SMG-style (frequency × occupancy); they describe this project's maths and
> claim no official compliance.

## Core definitions

- **Available hours**: teaching days × 9 h (09:00–18:00 Mon–Fri). Teaching
  days = `dim_date` rows with `teaching_week > 0`, not weekend, not holiday
  (64 days → 576 h/space on the small profile).
- **Frequency rate** = timetabled (booked) hours ÷ available hours.
- **Occupancy rate** = average group size ÷ room capacity, over booked events
  (`mart_space_utilisation` uses booked group sizes as the attendance proxy).
- **Utilisation** = frequency × occupancy.
- **No-show** = booked event with occupancy-sensor coverage whose maximum
  valid observed count in the event window is < 1. Events with no sensor
  coverage are *unknown*, never no-shows. Negative readings are invalid and
  excluded (222 readings, 0.09% — DQ territory).
- **Capacity mismatch** = group size < 50% of room capacity.
- **m² per FTE** = department NIA ÷ staff (or student) FTE; variance vs the
  cross-department median. Space→department mapping comes from truth spaces
  at P06 level until `dim_space` carries it (see `model.md`).
- **What-if releasable rooms** = n × (1 − utilisation/target).

## Limits

- Observed occupancy exists for ~28% of events (30 sensors); no-show
  conclusions only cover sensor-fitted rooms.
- Observed counts are headcount samples, not registers; the <1.0 threshold
  is a booked-but-empty proxy, not proof of absence.
- Single quarter (Jan–Mar 2026): no vacation/peak-season comparison.
