<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). CI fails if this page is stale. -->

# Data quality scores (generated)

Measured, not asserted: the numbers come from the P03 run.

Run `r7`. Scores come from `data/quality/gold/dq_scores.csv`; nothing is recalculated here.

## By dataset

| Dataset | Score | Checks | Read |
|---|---|---|---|
| assets | 99.7 | 10 | small number of failures |
| bms | 100.0 | 7 | clean at this window's checks |
| inspections | 99.4 | 9 | small number of failures |
| meters_a | 85.8 | 18 | needs attention |
| meters_b | 82.9 | 18 | below the 95% review threshold |
| sensors | 93.2 | 14 | needs attention |
| spaces | 99.9 | 15 | small number of failures |
| timetable | 93.0 | 15 | needs attention |
| work_orders | 95.3 | 23 | small number of failures |

## By dataset and dimension

| Dataset | Dimension | Score | Checks |
|---|---|---|---|
| assets | completeness | 100.0 | 2 |
| assets | referential_integrity | 100.0 | 2 |
| assets | uniqueness | 100.0 | 2 |
| assets | validity | 99.2 | 4 |
| bms | completeness | 100.0 | 2 |
| bms | reconciliation | 100.0 | 2 |
| bms | timeliness | 100.0 | 1 |
| bms | uniqueness | 100.0 | 1 |
| bms | validity | 100.0 | 1 |
| inspections | completeness | 100.0 | 2 |
| inspections | consistency | 92.5 | 1 |
| inspections | reconciliation | 100.0 | 2 |
| inspections | referential_integrity | 100.0 | 2 |
| inspections | uniqueness | 100.0 | 1 |
| inspections | validity | 100.0 | 1 |
| meters_a | completeness | 100.0 | 2 |
| meters_a | consistency | 80.4 | 4 |
| meters_a | reconciliation | 83.9 | 6 |
| meters_a | referential_integrity | 50.0 | 1 |
| meters_a | timeliness | 62.5 | 1 |
| meters_a | uniqueness | 100.0 | 1 |
| meters_a | validity | 100.0 | 3 |
| meters_b | completeness | 100.0 | 2 |
| meters_b | consistency | 95.7 | 4 |
| meters_b | reconciliation | 66.7 | 6 |
| meters_b | referential_integrity | 72.7 | 1 |
| meters_b | timeliness | 54.5 | 1 |
| meters_b | uniqueness | 100.0 | 1 |
| meters_b | validity | 99.9 | 3 |
| sensors | completeness | 100.0 | 2 |
| sensors | consistency | 97.6 | 1 |
| sensors | reconciliation | 84.9 | 6 |
| sensors | referential_integrity | 98.9 | 1 |
| sensors | timeliness | 100.0 | 1 |
| sensors | uniqueness | 100.0 | 1 |
| sensors | validity | 99.9 | 2 |
| spaces | completeness | 100.0 | 2 |
| spaces | consistency | 100.0 | 2 |
| spaces | reconciliation | 99.8 | 6 |
| spaces | referential_integrity | 100.0 | 1 |
| spaces | uniqueness | 100.0 | 1 |
| spaces | validity | 99.9 | 3 |
| timetable | completeness | 100.0 | 2 |
| timetable | consistency | 100.0 | 1 |
| timetable | reconciliation | 85.5 | 7 |
| timetable | referential_integrity | 100.0 | 1 |
| timetable | uniqueness | 100.0 | 1 |
| timetable | validity | 99.8 | 3 |
| work_orders | completeness | 100.0 | 2 |
| work_orders | consistency | 100.0 | 2 |
| work_orders | reconciliation | 87.9 | 9 |
| work_orders | referential_integrity | 100.0 | 1 |
| work_orders | timeliness | 100.0 | 1 |
| work_orders | uniqueness | 100.0 | 1 |
| work_orders | validity | 99.9 | 7 |

## Failing checks in this run

| Dataset | Check | Dimension | Severity | Rows failed | Rows checked | Threshold |
|---|---|---|---|---|---|---|
| assets | assets_install_not_future | validity | error | 42 | 1496 | 100.0 |
| meters_a | ma_id_known | referential_integrity | error | 8 | 16 | 100.0 |
| meters_a | ma_timeliness_per_meter | timeliness | error | 6 | 16 | 100.0 |
| meters_a | ma_recall_nulls | reconciliation | error | 1 | 207 | 100.0 |
| meters_a | ma_recall_out_of_range | reconciliation | error | 4 | 156 | 100.0 |
| meters_a | ma_recall_misspelt_category | reconciliation | error | 146 | 156 | 100.0 |
| meters_b | mb_id_known | referential_integrity | error | 3 | 11 | 100.0 |
| meters_b | mb_no_future_ts | validity | error | 96 | 34349 | 100.0 |
| meters_b | mb_timeliness_per_meter | timeliness | error | 5 | 11 | 100.0 |
| meters_b | mb_recall_misspelt_category | reconciliation | error | 3 | 3 | 100.0 |
| meters_b | mb_recall_future_dates | reconciliation | error | 2 | 2 | 100.0 |
| sensors | sensors_id_known | referential_integrity | error | 1 | 91 | 100.0 |
| sensors | sensors_value_non_negative | validity | error | 1422 | 773974 | 100.0 |
| sensors | sensors_recall_misspelt_category | reconciliation | error | 1583 | 1750 | 100.0 |
| sensors | sensors_recall_future_dates | reconciliation | error | 3 | 1166 | 100.0 |
| spaces | spaces_bronze_covers_truth | reconciliation | error | 5 | 500 | 100.0 |
| spaces | spaces_capacity_non_negative | validity | error | 2 | 495 | 100.0 |
| timetable | tt_no_future_date | validity | error | 36 | 12347 | 100.0 |
| timetable | tt_event_id_pattern | validity | error | 43 | 12347 | 100.0 |
| timetable | tt_recall_duplicates | reconciliation | error | 1 | 75 | 100.0 |
| timetable | tt_recall_orphan_fk | reconciliation | error | 3 | 3 | 100.0 |
| work_orders | wo_id_pattern | validity | error | 20 | 5938 | 100.0 |
| work_orders | wo_labour_non_negative | validity | error | 27 | 5938 | 100.0 |
| work_orders | wo_recall_duplicates | reconciliation | error | 1 | 36 | 100.0 |
| work_orders | wo_recall_orphan_fk | reconciliation | error | 3 | 3 | 100.0 |
| inspections | insp_completed_sane | consistency | warn | 3 | 40 | 100.0 |
| meters_a | ma_day_completeness | consistency | warn | 655 | 870 | 98.0 |
| meters_a | ma_volume_3sigma | consistency | warn | 3 | 91 | 100.0 |
| meters_b | mb_day_completeness | consistency | warn | 63 | 738 | 98.0 |
| meters_b | mb_volume_3sigma | consistency | warn | 8 | 93 | 100.0 |
| sensors | sensors_volume_3sigma | consistency | warn | 200 | 8281 | 100.0 |

## Alerts

| Kind | Dataset | Detail |
|---|---|---|
| error_fail | assets | check assets_install_not_future failed (severity error) |
| error_fail | meters_a | check ma_id_known failed (severity error) |
| error_fail | meters_a | check ma_timeliness_per_meter failed (severity error) |
| error_fail | meters_b | check mb_id_known failed (severity error) |
| error_fail | meters_b | check mb_no_future_ts failed (severity error) |
| error_fail | meters_b | check mb_timeliness_per_meter failed (severity error) |
| error_fail | sensors | check sensors_id_known failed (severity error) |
| error_fail | spaces | check spaces_bronze_covers_truth failed (severity error) |
| error_fail | timetable | check tt_no_future_date failed (severity error) |
| error_fail | sensors | check sensors_value_non_negative failed (severity error) |
| error_fail | spaces | check spaces_capacity_non_negative failed (severity error) |
| error_fail | timetable | check tt_event_id_pattern failed (severity error) |
| error_fail | work_orders | check wo_id_pattern failed (severity error) |
| error_fail | work_orders | check wo_labour_non_negative failed (severity error) |
| error_fail | meters_a | check ma_recall_nulls failed (severity error) |
| error_fail | meters_a | check ma_recall_out_of_range failed (severity error) |
| error_fail | meters_a | check ma_recall_misspelt_category failed (severity error) |
| error_fail | meters_b | check mb_recall_misspelt_category failed (severity error) |
| error_fail | meters_b | check mb_recall_future_dates failed (severity error) |
| error_fail | sensors | check sensors_recall_misspelt_category failed (severity error) |
| error_fail | sensors | check sensors_recall_future_dates failed (severity error) |
| error_fail | timetable | check tt_recall_duplicates failed (severity error) |
| error_fail | timetable | check tt_recall_orphan_fk failed (severity error) |
| error_fail | work_orders | check wo_recall_duplicates failed (severity error) |
| error_fail | work_orders | check wo_recall_orphan_fk failed (severity error) |

All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any real university, building or estate, and nothing here is a compliance statement.
