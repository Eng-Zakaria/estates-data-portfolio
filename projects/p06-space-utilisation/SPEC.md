# P06 SPEC (copy of docs/specs section - traceability)

## P06: Space utilisation

**Location:** `projects/p06-space-utilisation/`
**Criteria:** E5, E6, D5
**Business questions:** Which rooms are booked but not used? How much space do we have per person by department? How much space could be released at a target utilisation?

### Gold inputs
`dim_space, dim_building, dim_department, dim_date, fct_timetable_event, fct_space_observed_occupancy` (from sensors or survey-style samples; produced with P17 when available, otherwise from the foundation's occupancy model).

### KPIs (SMG-style frequency × occupancy; state the definitions in `methodology.md`)
- **Frequency rate** = timetabled hours ÷ available hours (core window and teaching weeks configurable, default 09:00-18:00 Mon-Fri).
- **Occupancy rate** = average attendance ÷ room capacity while in use.
- **Utilisation** = frequency × occupancy.
- m² NIA per staff FTE / per student FTE; space share by category; cost per m²; **no-show rate** (booked, observed occupancy ≈ 0); **capacity mismatch** (group size < 50% of capacity).

### Pages
1. **Executive overview:** KPI cards, utilisation by building, trend by teaching week.
2. **Heatmap:** day × hour utilisation matrix with building/room-type slicers.
3. **Rooms to review:** table of low-utilisation and high-no-show rooms, conditional formatting, tooltip page with weekly profile, drill-through to a room page.
4. **Department allocation:** m² per FTE vs institutional median (bar + variance), category mix.
5. **What-if:** parameter for target utilisation → estimated rooms/m² releasable.

### DAX measures required (write full DAX in `measures.dax` with comments)
`Available Hours, Timetabled Hours, Frequency %, Avg Occupancy %, Utilisation %, No-show %, NIA m², m² per Staff FTE, m² per Student FTE, Variance to Median, Releasable m² (what-if), Utilisation vs Target`.

### Planted findings to surface
B003 teaching rooms (booked ≥ 70% but occupancy < 30%); department D-ENG ≈ 40% above median m²/FTE.

### Acceptance
- Validation SQL reproduces every headline KPI; values tie to the Power BI numbers within rounding.
- `wireframe.md` specifies all 5 pages in enough detail to build without guessing.
- Unit tests for the KPI SQL on a hand-computed fixture (e.g., one room, 3 events).
- Planted findings are visible in the first two pages (documented with the exact filter to see them).

---
