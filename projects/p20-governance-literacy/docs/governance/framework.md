# Governance framework

The estate runs on facts that arrive from many systems. This framework says who owns those facts, who may change what they mean, and how to settle disagreements. It is a proposal for ratification, not a description of an existing committee.

## Principles

1. **One owner per dataset.** Every dataset has a named accountable owner. "The estates team" is not an owner.
2. **The definition belongs to the business, the implementation to the analyst.** Analytics can propose a change to a metric. Only the accountable owner can approve it.
3. **Publish the caveats with the number.** A metric with a hidden limitation is worse than no metric, because it gets quoted.
4. **Show the data quality, not a claim of it.** Every published page carries the current quality score and the date the data was refreshed.
5. **Synthetic means labelled.** Anything generated rather than measured is labelled as such on the page, not in a footnote nobody reads.
6. **Standards are cited, not remembered.** A rule from a standard is used only from an official source, recorded with its version and licence.
7. **Reproducible beats clever.** A colleague must be able to rebuild every published number from the README commands.
8. **Small is reversible.** Prefer a definition you can change next term over a clever one that is hard to unwind.
9. **No personal data in analytics.** Estates analytics uses headcounts and asset records, not people. See [data classification and handling](../data/classification.md).
10. **Errors are published, not hidden.** A failing check or a wrong number is fixed or explained; it is never quietly dropped from the dashboard.

## Roles

Four roles, defined in full on the [roles page](roles.md). In one line each:

- **Owner (accountable)**: the estates manager answerable for the outcome the data supports, and the only person who can approve a change to a definition or threshold.
- **Steward**: the person who looks after definitions day to day, sets quality expectations, and answers questions from users.
- **Custodian**: the person who keeps the pipeline honest: loading, tests, documentation and access.
- **Consumer**: everyone who uses a dashboard, report or extract, and who quotes the definition when they use a number.

The generated [RACI](generated/raci.md) shows who fills each role for space, assets, energy and carbon, compliance, and BIM.

## Decision rights

| Decision | Who decides | Who must be asked | What happens after |
|---|---|---|---|
| Change a metric definition or formula | Owner for the domain | Steward, custodian | Version bump in [the change log](../process/metric-change-log.md), page regenerated, users told |
| Set a target or threshold (SLA, utilisation target, baseline year) | Owner for the domain | Steward | Recorded in the change log with the reason |
| Publish or withdraw a dashboard | Analytics lead, on the owner's approval | Owner, steward | CI green, page carries DQ score and refresh time |
| Change a data classification | Owner | Data protection contact (awareness-level advice here, not legal advice) | Classification page updated |
| Adopt or retire a standard | Owner for the domain | Steward | [Standards register](generated/standards-register.md) status updated with the source |
| Accept a project's information handover | Owner for BIM | Project manager, custodian | Register updated, crosswalk rebuilt, diff archived |
| Stop a publication for safety reasons | Owner for the domain | Nobody needs to be asked first | Reason logged; publication resumes when cleared |

## Escalation path

Use the shortest route that fits. Record what you asked and when, because "I told them" is not a path.

| Situation | Route | Target time |
|---|---|---|
| A published number is wrong | Consumer to steward, steward to custodian | Same working day if the number is being quoted in a decision |
| A dashboard disagrees with a room sheet or job list | Steward, then custodian | 2 working days |
| Two teams want different definitions of the same measure | Both stewards, then both owners, then estates director | 10 working days |
| A metric definition is disputed and changes a published number | Owner decides; change log records the reason | Next reporting cycle at the latest |
| Data has been lost or is corrupted | Custodian immediately as an incident, owner informed | Immediate |
| A failed inspection or a safety-relevant record is missing | Owner for compliance, escalate to estates director | Immediate |
| Personal data appears in a published report | Custodian removes it, owner and data protection contact informed | Immediate |
| A standard is needed but not held | Steward logs it in the repository's open questions | Next review |

## What is deliberately not decided here

- **Pay and performance.** No metric in this pack is tied to individual performance. Utilisation and MTTR are used to plan work, not to judge a team.
- **Legal interpretation.** Statutory inspection frequencies in the demo data are illustrative. In a real estate the compliance owner supplies them from the legal source, and this pack records where they came from.
- **Contractor performance scoring.** The maintenance measures include contractor names for filtering, not for league tables.