# P06 findings (small profile, seed 42 — synthetic)

## Estate headline (`v01`)
495 spaces, 24,052 timetabled hours over 576 available hours/space:
frequency **8.4%**, occupancy **15.7%**, utilisation **4.2%**. Low overall —
driven by 360 never-booked rooms (see `v02` bottom/top of the review table).

## Planted finding 1: B003 teaching rooms — PRESENT IN WEAKER FORM
Spec predicts booked ≥ 70% with occupancy < 30%. Measured (`v05`):
**zero** rooms clear 70% frequency. But the occupancy half holds for all
30 rooms (0.20–0.23), and B003 teaching frequency (0.50–0.61, avg 0.556) is
nearly double the teaching average (0.309) while occupancy (0.215) is far
below it (0.566). Closest filter: `frequency_rate >= 0.50 AND
occupancy_rate < 0.30` → all 30 B003 teaching rooms. The booked-but-empty
story is real; the 70% threshold is not met on small — report measured.

## Planted finding 2: D-ENG m²/FTE — DOES NOT MATCH SPEC MAGNITUDE
Measured (`v04`): D-ENG 247.5 m²/staff-FTE vs median 64.3 → **+285%**,
not the spec's ≈40%. D-ENG holds 14,852 m² across 181 spaces (labs
included). Either the intended metric differs (e.g. office-only space) or
the planting targets the default profile. Exact filter documented in
`v04`; report measured, do not force ≈40%.

## No-shows and mismatch (`v02`)
- 3,336/12,026 events (28%) have sensor coverage; **3 no-shows** — the
  synthetic estate shows up. Page 3 works; the number is ~0%.
- **6,704 events (56%) are capacity mismatches** — the actionable story
  for the rooms-to-review page.
- 222 negative readings excluded as invalid (29 sensors).
