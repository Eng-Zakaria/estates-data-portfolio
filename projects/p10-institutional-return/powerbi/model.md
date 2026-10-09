# P10 Power BI model (synthetic, optional one-pager)

## Tables and columns used

| Table | Grain | Key columns used |
|---|---|---|
| building_areas | building × category | building_id, return_category, nia_m2, gia_m2 |
| energy | building × utility | building_id, utility, kwh |
| emissions | building × fuel | building_id, fuel, kgco2e |
| costs | building × trade | building_id, trade, cost_gbp |
| cost_allocation | pool × activity | pool, activity, allocated_gbp, driver_total |
| validation_report | violation | rule_id, rule_name, severity, message |

## Relationships

No relationships needed (flat tables). Use slicers on building_id, return_category, pool, activity.

## Measures (DAX)

```dax
Total NIA = SUM(building_areas[nia_m2])
Total GIA = SUMX(VALUES(building_areas[building_id]), CALCULATE(MAX(building_areas[gia_m2])))
Total Energy kWh = SUM(energy[kwh])
Total CO2e = SUM(emissions[kgco2e])
Pool Total = SUM(cost_allocation[allocated_gbp])
Validation Blocking = COUNTROWS(FILTER(validation_report, validation_report[severity]="blocking"))
Validation Query = COUNTROWS(FILTER(validation_report, validation_report[severity]="query"))
```

## Wireframe — one page

```
+----------------------------------------------------------+
| KPI: Total NIA | Total GIA | Energy kWh | CO2e | Pool £  |
+----------------------------------------------------------+
| Table: Validation report (rule, severity, message)       |
|   Conditional formatting: blocking=red, query=amber      |
+----------------------------------------------------------+
| Bar: Cost allocation by pool → Teaching/Research/Other   |
+----------------------------------------------------------+
```