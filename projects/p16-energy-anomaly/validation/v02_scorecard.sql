-- v02_scorecard.sql — reproduce the scorecard parquet independently.
-- Ties to: page 1 table and the [Attributed £/yr] KPI card.
--
-- The pipeline attributes savings to flagged fault modes only:
--   high_overnight_baseload -> overnight excess
--   spike | step_change | gradual_drift -> residual excess above 3 robust sd
--   flatline_meter_fault | missing_data -> £0 (use cannot be estimated)
-- Reading the parquet directly is the tie-out for the Power BI numbers:
--
--   SELECT * FROM read_parquet('projects/p16-energy-anomaly/outputs/building_scorecard.parquet')
--   ORDER BY gbp_year DESC;
--
-- Expected (seed 7, small + default-cache profile, 18 meters):
--   row 1  M-B007-E01  B007  27918.7 kWh   £7817.23
--   row 2  M-B019-G01  B019   2912.0 kWh   £815.37
--   row 3  M-B008-E01  B008    310.8 kWh   £87.03
--   row 4  M-B004-E01  B004    189.8 kWh   £53.14
--   row 5  M-B006-E01  B006     64.5 kWh   £18.05
--   clean meters (e.g. M-B001-E01) -> kwh_year 0.0, gbp_year 0.00
SELECT
    meter_id,
    building,
    source,
    ROUND(peak, 2) AS peak_kwh_period,
    types,
    kwh_year,
    gbp_year,
    ROUND(gbp_year / NULLIF(kwh_year, 0), 4) AS implied_tariff_gbp_per_kwh,
    ROUND(0.75 * kwh_year, 1) AS kwh_lo,
    ROUND(1.25 * kwh_year, 1) AS kwh_hi
FROM read_parquet('projects/p16-energy-anomaly/outputs/building_scorecard.parquet')
ORDER BY gbp_year DESC;