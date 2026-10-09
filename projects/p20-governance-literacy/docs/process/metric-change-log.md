# Metric change log

Every change to a published number, with the reason. Newest first. Format: date, metric id, version, change, reason, owner, impact.

The full list of current definitions and versions is the generated [metric registry](../generated/metric-registry.md).

## Entries

| Date | Metric | Version | Change | Reason | Owner | Impact |
|---|---|---|---|---|---|---|
| 2026-10-08 | all (`*` 1.0.0) | 1.0.0 | Registry created with 53 entries: 48 published on dashboards, 5 planned. | Governance pack: publish definitions, owners and caveats with every dashboard number | estates-analytics | None. Numbers unchanged; definitions were previously scattered in the Power BI handoff notes |
| 2026-10-08 | `baseload_pct` | 1.0.0 | Overnight window and divisor recorded as conventions in the registry; no gold column yet. | Number was published without its window defined | estates-energy | None to the value; readers can now see what it means |
| 2026-10-08 | `no_show_pct` | 1.0.0 | Denominator recorded as covered events only; uncovered events excluded, not counted as no-shows. | The calculated column's coverage rule was buried in a comment | estates-planning | None to the value; clarifies why the number moves when sensors are added |
| 2026-10-08 | `compliance_days_overdue` | 1.0.0 | As-of date declared part of the definition. | Overdue counts were being read against today's date | estates-hs | None to the value; the page now always shows the as-of date |

## How to add an entry

1. Change the definition in `metrics.yml` and bump `version` (major if the number changes meaning, minor if only the wording or caveats change).
2. Add the row above with the reason in one sentence and the impact in one sentence. "None" is a valid impact; so is "all carbon figures restated".
3. Run `make p20-build` and `make p20-check`.
4. If consumers need telling, do it before publication, not after.

## What does not go in the log

- Wording fixes that do not change meaning (those are a minor version bump, no announcement).
- Data corrections. Those go in the [runbooks](../runbooks.md) as incidents, with the affected dates.
- Drafts. Log it when it is published.

## Reading the log as evidence

For a hiring panel or an auditor, this table answers two questions quickly: has the estate changed a published number quietly, and who decided? The answer here is four entries, all in one day, all from standing up the governance pack. A real estate accumulates entries over years, and the volume of "impact: consumers told" rows is a good sign rather than a bad one.