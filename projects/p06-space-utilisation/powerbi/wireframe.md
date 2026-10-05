# P06 wireframe — Space utilisation (5 pages, synthetic)

Footer on every page: *"Synthetic data for portfolio demonstration."*
Slicers global: building, space category, teaching week.

## Page 1 — Executive overview (purpose: how well used is the estate?)

```
+----------------------------------------------------------+
| KPI cards: Frequency % | Avg Occupancy % | Utilisation % |
| Timetabled Hours | No-show %                              |
+----------------------------------------------------------+
| Bar: utilisation by building (B003 flagged, v05 filter)  |
+----------------------------------------------------------+
| Line: utilisation trend by teaching week                 |
+----------------------------------------------------------+
```

## Page 2 — Heatmap (purpose: when is space used?)

```
+----------------------------------------------------------+
| Matrix: day (Mon-Sun) x hour (08-18), colour = events   |
|  in progress (source: v03; slicers: building, category)  |
+----------------------------------------------------------+
```

## Page 3 — Rooms to review (purpose: which rooms need action?)

```
+----------------------------------------------------------+
| Table (v02): room | building | category | util % | freq% |
| occ% | no-shows | no-coverage events | mismatch events    |
| Conditional formatting: util < 10% red; no-show > 0 flag |
+----------------------------------------------------------+
| Tooltip page: weekly booked profile for the room         |
| Drill-through: room page (events + observed overlay)     |
+----------------------------------------------------------+
```

## Page 4 — Department allocation (purpose: who holds the space?)

```
+----------------------------------------------------------+
| Bar + variance: m2 per staff FTE vs median (v04; D-ENG   |
|  measured +285% — report as measured, see findings)      |
+----------------------------------------------------------+
| Donut: NIA share by category                             |
+----------------------------------------------------------+
```

## Page 5 — What-if (purpose: what could be released?)

Parameter: target utilisation (default 40%). Visuals: releasable rooms/m²
cards + ranked release-candidate table (lowest utilisation first).
Bookmarks: "Small-profile view" vs "Full-year view".
