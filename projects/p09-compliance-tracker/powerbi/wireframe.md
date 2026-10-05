# P09 wireframe — Compliance tracker (5 pages, synthetic)

Footer on every page: *"Synthetic data for portfolio demonstration."*

## Page 1 — Executive RAG matrix (purpose: what's the estate compliance picture?)

```
+----------------------------------------------------------+
| KPI cards: Total | Overdue | Due 30d | Failed+Remedial  |
+----------------------------------------------------------+
| Matrix: Building (rows) × Inspection Type (cols)         |
|  Cell = RAG (Green/Amber/Red) with tooltip: status, days |
|  Slicers: building, type, date range                     |
+----------------------------------------------------------+
```

## Page 2 — Overdue list (purpose: what needs action now?)

```
+----------------------------------------------------------+
| Table: Inspection | Building | Type | Due | Days overdue |
| Result | Remedial? | Contractor                              |
| Conditional formatting: >90d red, 31-90 amber, ≤30 yellow|
| Drill-through to building page (page 1 filtered)         |
+----------------------------------------------------------+
```

## Page 3 — Next 90 days calendar (purpose: what's coming up?)

```
+----------------------------------------------------------+
| Calendar matrix: Week (rows) × Type (cols), count per cell|
| Table below: due date | building | type | contractor      |
| Slicer: week range, type                                 |
+----------------------------------------------------------+
```

## Page 4 — Remedial ageing (purpose: which fixes are stuck?)

```
+----------------------------------------------------------+
| Table: Remedial | Building | Opened | Closed | Ageing (d)|
| Band (≤30 green / 31-90 amber / >90 red) | Contractor   |
| KPI cards: open count | >90d count | total cost estimate |
+----------------------------------------------------------+
```

## Page 5 — Compliance trend (purpose: are we improving?)

```
+----------------------------------------------------------+
| Line: Monthly overdue count + failed+remedial open (12m)|
| Bar: monthly compliant %                                  |
| Slicer: building, type                                    |
+----------------------------------------------------------+
```

## Bookmarks
- "Small-profile view" (Jan–Mar 2026)
- "Trend view" (synthetic 12 months)