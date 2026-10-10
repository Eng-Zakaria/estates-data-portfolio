# Runbooks

*All data referenced here is synthetic: no real estate, building, person or compliance status is described.*

What to do when something breaks. Each runbook says the symptom, the first three checks, the fix, who to tell, and what to write down.

Order of response, always: **stop the wrong number reaching people, then find the cause, then fix it.**

Two roles appear throughout: the **custodian** handles the pipeline, the **steward** handles meaning and users. Escalate to the **owner** when the fix changes a published number or a threshold.

## RB1: an error-severity check failed

**Symptom:** CI is red; a publish is blocked; the DQ score page lists a failing check.

1. Read the failing check row: dataset, dimension, rows failed, rows checked, threshold.
2. Open the failed rows output for that dataset. It keeps the rows and the reason they were held back.
3. Confirm the direction: is the source sending less, more, or different data?

**Fix:** if it is a genuine source change, update the staging model or the check threshold, and record why. If it is a real defect, the rows stay quarantined and the owner decides whether to publish with the gap.

**Tell:** custodian immediately, steward the same day. Owner if publication is delayed.

**Write down:** the check, the rows affected, the cause, the fix, and whether the fix changes any published number.

## RB2: a published number moved sharply

**Symptom:** a dashboard or report number differs a lot from last period with no obvious cause.

1. Check the DQ page: has a score dropped or an alert been raised?
2. Check the metric version in the [registry](generated/metric-registry.md): did a definition change?
3. Check the filter and the as-of date: is this the same scope as last time?

**Fix:** if the cause is a definition change, follow the change process and publish both numbers side by side for one cycle. If it is a data gap, say so on the page rather than leaving the number to be misread.

**Tell:** steward, then everyone who used the old number.

**Write down:** an entry in the [metric change log](process/metric-change-log.md) if the definition moved; an incident note otherwise.

## RB3: a dashboard and a source system disagree

**Symptom:** someone says the room sheet, the job list or the meter bill does not match the report.

1. Reproduce it with the report's validation query. Same number or not?
2. If yes, the disagreement is in meaning, not data: compare definitions, filters and the as-of date.
3. If no, find the first layer where the two diverge, using the [lineage page](generated/lineage.md).

**Fix:** correct the load or the transformation, never the report, unless the report is the thing that is wrong.

**Tell:** steward, and the person who reported it, even if they were right to doubt it.

**Write down:** what diverged, at which layer, and the test that now catches it.

## RB4: a check is failing on data that should not exist

**Symptom:** a uniqueness or foreign key check fails on a dimension table.

1. Confirm the grain is what the model says. A grain mistake looks exactly like this.
2. Look for a source that now sends two rows where it used to send one, or a new source merged into the wrong staging table.
3. Decide: dedupe with a documented rule, or fix the source?

**Fix:** fix the source when you can. A dedupe rule is a decision that needs an owner, because it discards data.

**Tell:** custodian and owner. Never silently dedupe a dimension table.

**Write down:** the rule, the rows removed, and the check that now proves uniqueness.

## RB5: the pipeline did not run, or ran but published nothing

**Symptom:** no new data; a report is showing old dates.

1. Check the orchestrator status and the last successful run.
2. Check whether the source actually sent a file: an empty drop is a valid file that looks like an outage.
3. Check the freshness check: it compares against the data window, not the wall clock.

**Fix:** for an empty drop, record it and keep the previous published state visible with its date. Do not publish an empty report as if it were current.

**Tell:** steward, and anyone with a fixed reporting date.

**Write down:** start time, end time, cause, and what was published instead.

## RB6: personal or confidential data reached a published page

**Symptom:** a name, a phone number, a commercial figure or a security detail appears in a report or extract.

1. **Unpublish or re-export immediately.** This comes before finding the cause.
2. Record what was exposed, where it went, and how many records.
3. Tell the owner and the data protection contact the same day.
4. Then find the column that carried it, filter it at load time, and add a check so the build fails next time.

**Tell:** owner, data protection contact, and anyone who received the export.

**Write down:** an incident note with the timeline. The [classification page](data/classification.md) lists the estates cases.

## RB7: a generated page is out of date

**Symptom:** `make p20-check` reports a stale page.

1. Run `make p20-build` and read the diff.
2. If the diff is expected, the change came from the dbt project, the DQ output or the YAML sources.
3. If it is not expected, find which source moved before committing.

**Fix:** commit the regenerated page with the source change in the same commit. A regenerated page on its own has no explanation.

**Tell:** nobody, unless the diff changes a published number, in which case RB2 applies.

## RB8: someone wants to know why a number means what it means

**Symptom:** a question about a definition, not a defect.

1. Look it up in the [registry](generated/metric-registry.md), then the [glossary](generated/glossary.md).
2. Give the definition, the caveats, the owner, the version and the as-of date.
3. If it is not registered, that is a gap: log it as a request and say so.

**Tell:** the person who asked, and add the gap to the next steward review.

## The first five questions for any incident

1. Is a wrong number with people right now? If yes, stop that first.
2. What is the as-of date of the affected report?
3. Is there a failing check or a metric version change that explains it?
4. Who used the number, and did they act on it?
5. What test will catch this next time?
