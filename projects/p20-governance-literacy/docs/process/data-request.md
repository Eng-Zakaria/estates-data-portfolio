# Data request and change process

*All data referenced here is synthetic: no real estate, building, person or compliance status is described.*

Two queues, one inbox address. Requests for data and requests to change a published number follow different paths because the second one changes what people have already quoted.

## Queue 1: data requests

### Intake form

Copy this into an email or a ticket. Short forms get answered faster because the steward does not have to ask four questions back.

```
1. What do you need?          (one sentence: "monthly gas kWh per building for B001-B004")
2. Why?                      (the decision it supports, one sentence)
3. Who is asking, and which team?
4. Grain and period           (per meter per month, 2025-01 to 2026-03)
5. Columns or measures        (exact names if you already know them)
6. Format and destination     (Power BI, spreadsheet, API, parquet, a page on the site)
7. Classification            (public / internal / confidential)
8. Is personal data involved? (yes/no; if yes, describe the fields)
9. When do you need it?       (date, and whether it is fixed, e.g. a committee date)
10. What have you already tried?
```

### Triage criteria

Requests are sorted into four bands, and the band decides who handles it and when.

| Band | Looks like | Owner | Response |
|---|---|---|---|
| A: asked and answerable | existing table, existing measure, no new logic | steward | answer or link, 2 working days |
| B: existing data, new shape | needs a query, a filter or an export | steward with analyst | first answer, 5 working days |
| C: new metric or new source | needs a definition, an owner decision or a new feed | owner decides, analyst builds | decision in 10 working days, build scheduled after |
| D: not a data request | asks for advice, a judgement or a policy | refer to the right person | acknowledged the same day |

Two rules that keep triage fast:

- If the request needs a new definition, it is band C even if the data exists. Publishing a number nobody has agreed means is how definitions drift.
- If it needs a new source system, it is band C and needs a licence check before anything is loaded.

### Service levels

| Event | Target |
|---|---|
| Acknowledge any request | 1 working day |
| Band A answered | 2 working days |
| Band B first answer | 5 working days |
| Band C decision on whether to do it | 10 working days |
| Band D referred | same day |
| Change request: decision | 10 working days |
| Change request: published | next scheduled release after approval |
| Broken published number | same working day if it is being quoted |

### What you get, and what you do with it

Every answer comes with: the definition used, the as-of date, the refresh frequency, the current DQ score, and the classification. If any of those are unknown, the answer says so rather than staying silent.

## Queue 2: change requests

A change request is any of:

- a different definition or formula for a published metric;
- a different threshold, target, band or SLA;
- adding a measure to a dashboard, or removing one;
- changing which source a metric reads.

### Steps

1. **Raise it** with the intake form plus: the metric id from the [registry](../generated/metric-registry.md), what changes, and why.
2. **Steward triage** within 2 working days: is this a genuine error, a genuine improvement, or a preference?
3. **Owner decision** within 10 working days. The owner decides, and the steward records the reasoning in one paragraph.
4. **Impact check** before anything is published: which dashboards, reports and saved extracts used the old definition, and who needs telling.
5. **Version bump** in `metrics.yml` and an entry in the [metric change log](metric-change-log.md).
6. **Regenerate and publish**: `make p20-build`, tests, CI, then the page refresh with the new version visible.
7. **Tell the consumers** who used the old number, with both numbers, side by side, for one reporting cycle.

### Rejected or deferred changes

Common and legitimate reasons:

- the definition is right but the data cannot support it yet (say which gap, and what would close it);
- it would make a published number move for reasons unrelated to performance;
- it duplicates an existing metric under a new name;
- the cost is high and the decision it supports can be made another way.

A rejected request still gets an answer with a reason. Silence is the only unacceptable outcome.

## Emergency path

If a published number is being quoted in a decision and is wrong:

1. Say so in the same channel the number was quoted in, the same day, with the size of the error.
2. Withdraw or annotate the number; do not wait for a tidy fix.
3. Custodian finds the cause; steward finds who used it.
4. Fix, test, republish, then log it as an incident in the [runbooks](../runbooks.md).

## What this process does not cover

- Access requests for restricted datasets: these go through the owner named on the dataset in the [registry](../generated/metric-registry.md), not through this queue.
- Personal data access: follow the institution's process, not this one.
- Contractor and supplier queries: those go to the commercial team.
