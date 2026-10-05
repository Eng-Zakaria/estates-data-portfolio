# P08 Power BI model (synthetic)

Source: gold tables in `data/warehouse.duckdb` (or `data/gold/*.parquet`
extracts), loaded via `queries/*.pq`. Set the `GoldFolder` parameter to the
absolute `data/gold` path before refresh.

## Tables and columns used

| Table | Grain | Key columns used |
|---|---|---|
| dim_building | building | building_id, building_name, campus, gia_m2, primary_use, heating_fuel |
| dim_date | day | date_day, year, month, term, is_holiday, is_weekend |
| dim_emission_factor | fuel | fuel, scope, factor_kgco2e_per_kwh, factor_year |
| fct_energy_daily | meter × day | meter_id, building_id, utility, energy_date, kwh, peak_half_hour_kwh, hdd |
| fct_meter_hh | meter × HH | meter_id, ts_utc, value_kwh (page 3/4 only; consider aggregated import) |
| mart_carbon_monthly | month × fuel | month, fuel, kwh, kgco2e, baseline_kwh, variance_to_baseline |

Hidden: `meter_id` (use building names), `factor_year` (filter only),
`peak_half_hour_kwh` (intermediate), all surrogate/UTC internals.
Date table: use `dim_date[date_day]` as the single date dimension; mark it
as a date table. No RLS roles required (portfolio demo; note in build-guide
if building-manager RLS is wanted later — see P07 pattern).

## Relationships (single direction, many-to-one)

- fct_energy_daily[building_id] → dim_building[building_id]
- fct_energy_daily[energy_date] → dim_date[date_day]
- mart_carbon_monthly[fuel] → dim_emission_factor[fuel] (virtual; fuels differ
  by name — use TREATAS in measures instead of a physical relationship)
- fct_meter_hh[meter_id] → dim_meter[meter_id] (import dim_meter if HH page kept)

All filters flow one way (dims → facts). Keep `dim_emission_factor`
disconnected and apply factors with TREATAS (see measures.dax).
