# DQ Policy (P03)

Synthetic estate data quality policy. Every check maps to one of seven dimensions; severity drives the CI gate.

## Dimensions

| Dimension | Meaning | Example check |
|---|---|---|
| completeness | Mandatory fields present | `spaces_room_not_null` |
| uniqueness | Grain is unique | `spaces_room_unique` |
| validity | Values in domain/range | `spaces_nia_in_range` |
| consistency | Cross-field or cross-row logic holds | `wo_chronology` |
| timeliness | Data is fresh for its contract | `sensors_timeliness_per_sensor` |
| referential_integrity | FK joins resolve | `spaces_building_known` |
| reconciliation | Layer counts balance + planted defects detected | `spaces_reconciled`, `*_recall_*` |

## Severities and response

| Severity | Weight | Meaning | Response |
|---|---|---|---|
| error | 3 | Breaks a downstream KPI or hides data loss | Fails CI gate; `dq.alerts.error_fail`; human-reviewed within 24h |
| warn | 2 | Degrades analysis but pipeline continues | Logged; score deduction; reviewed weekly |
| info | 1 | Advisory | Logged only |

## Scoring

`score = 100 * sum(w * pass_rate) / sum(w)` per dataset and per (dataset, dimension). Building scores aggregate `by_building` SQL checks only. `pass_rate = 1 - rows_failed / rows_checked` (or `1 - planted/detected` for recalls).

## Thresholds

- Default `threshold: 100.0` (zero tolerance) for structural rules (uniqueness, FK, reconciliation).
- 95–99% for operational rules where rare valid exceptions exist (e.g. open WOs aged >90d, NIA ≤ GIA).
- DST and planted-defect rules use exact counts, not percentages.

## Alerts

- Any `error` check failing → `dq.alerts` row and CI red.
- Dataset score drop > 5 points vs trailing-7 mean → `dq.alerts.score_drop`.

## Recalls

Every planted defect type in `ground_truth.yaml` has a recall rule producing the detection percentage. Multi-hit rows are attributed to the first quarantine reason in the P01 pipeline order; Tier-2 bronze cross-match attributes overlap when a shortfall is seen. Recall below 100% on a deterministic type is a bug, not a data issue.

## Window and freshness

Synthetic window end `2026-04-01`. Timeliness checks compare against window end ±36h, not wall-clock now. Real feeds would use event-time vs ingest-time.

## Review cadence

- Daily: CI gate on error failures.
- Weekly: score trend in the snapshot checks.
- Per release: README §5 results table refreshed with measured numbers.
