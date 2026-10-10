# Roles

*All data referenced here is synthetic: no real estate, building, person or compliance status is described.*

Four roles, one per person where possible. A person can hold more than one role, but the accountable owner for a domain must be able to say no to a change.

## Owner

The estates manager answerable for the outcome the data supports.

- Owns the domain: space, assets, energy and carbon, compliance, or BIM.
- Approves definitions, formulas, grain, thresholds and targets.
- Signs off publication and can stop it.
- Is the escalation point when two teams disagree.

In this repository the owner ids map to estates roles, not to names: `estates-planning`, `estates-operations`, `estates-energy`, `estates-hs`, `estates-bim`, `estates-finance`. The [RACI](../generated/raci.md) names the accountable owner per activity.

## Steward

The person who looks after definitions day to day.

- Keeps the glossary and metric registry honest: definitions, caveats, versions.
- Answers "what does this number mean?" for users.
- Sets what quality is good enough for publication, in agreement with the owner.
- Runs the weekly review of failing checks and the monthly review of scores.
- Notices when a dashboard stops matching the estate and says so.

## Custodian

The person who keeps the pipeline trustworthy.

- Loads data, runs the tests, quarantines bad rows and keeps the reason.
- Enforces the naming and modelling standards: layers, key columns, units, timestamps in UTC.
- Publishes the data dictionary, lineage and DQ pages so users can see for themselves.
- Protects access: who can read what, and at what classification.
- Reports incidents quickly, with numbers rather than adjectives.

## Consumer

Everyone who uses the output.

- Reads the definition before quoting a number, and quotes it with the number.
- Uses the DQ score and the refresh time, and says "as at" when reporting.
- Reports a suspected problem rather than working around it.
- Does not quietly multiply numbers from different filters and add them up.

## Who does what in the daily cycle

| When | Who | What |
|---|---|---|
| Every pipeline run | Custodian | Checks run, failures quarantined, DQ results written |
| Every publish | Custodian then steward | Dictionary, lineage and DQ pages regenerated, CI green |
| Daily | Steward | Review error-severity alerts |
| Weekly | Steward and custodian | Review failing checks, coverage gaps, open metric changes |
| Monthly | Steward and owner | Refresh definitions, agree whether scores are publishable |
| Per release | Steward | Update the glossary, registry version, and this site |

## What a good hand-off looks like

- The new owner can answer "who changed this number and why?" from the change log alone.
- A new steward can rebuild a published figure from the README without help.
- A consumer can find the definition, the DQ score and the refresh time on one page.

If any of those is false, the answer belongs in the [data request process](../process/data-request.md), not in an inbox.
