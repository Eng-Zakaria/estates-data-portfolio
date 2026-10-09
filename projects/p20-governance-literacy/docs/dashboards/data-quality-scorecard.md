# Data quality scorecard

**Question it answers:** how much should I trust the other reports today?

**Refresh:** every pipeline run. The measured numbers are on the generated [DQ scores page](../generated/dq-scores.md).

**Who to ask:** the analytics custodian for a failing check; the steward for what it means.

## What a score means

Each dataset gets a score from 0 to 100. It is a weighted average of its check results, where an error-severity failure counts more than a warning. Every check belongs to one of seven kinds of test: completeness, uniqueness, validity, consistency, timeliness, referential integrity and reconciliation.

Scores also appear for each dimension within a dataset, and for each building. Those are the useful ones: a score that drops for one dimension on one building is an operational problem, not a broken pipeline.

## How to use it

1. Open the [DQ scores page](../generated/dq-scores.md) before a reporting deadline.
2. Look for **error-severity failures**. Any of those blocks publication.
3. Look at **score by dimension** for a dataset you care about. A falling completeness score usually means a source feed stopped sending a field.
4. Check **alerts**. A score drop of more than five points against the recent average is raised as an alert even when no check failed outright.

## Common misreadings

1. **A score is not a percentage of correct rows.** It is a weighted average of checks, so two datasets with the same score can be in very different states.
2. **A high score does not mean the data is right.** It means the checks we wrote passed. A check nobody wrote cannot fail.
3. **A low score is often a known gap.** Some datasets fail a check on purpose in the demo data so the mechanism is visible. Read the check list, not just the number.
4. **Scores move when the framework changes.** Compare like-for-like versions.
5. **Scores are per run.** A score without its date is not information.

## What the demo data shows

On the current run most datasets score above 95. The meter datasets score lowest, in the eighties, because supplier files carry duplicate and misaligned half hours that the pipeline quarantines. That is the framework working as intended: the bad rows are held back with a reason rather than passed through. Read the failing-check table on the generated page for the specifics.

## Limitations to say out loud

- The checks measure what this portfolio decided to check.
- Timeliness is measured against the end of the data window, not the wall clock, because the demo data is a fixed window.
- Scores do not measure the correctness of a definition, only of a record against that definition.

## When something fails

The [runbooks](../runbooks.md) page has the step-by-step response for each failure type, including who to tell and what to write down.