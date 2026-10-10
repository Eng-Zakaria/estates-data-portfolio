<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). CI fails if this page is stale. -->

# RACI (generated)

Who does what, who decides, and where problems go.

Generated from `raci.yml`. **A** is the single accountable role per activity. Letters: **A** Accountable - one name, answerable for the result, **C** Consulted - asked before the decision is made, **I** Informed - told after the decision, **R** Responsible - does the work.

## Roles

| Role | Accountable for | Typical person | Escalates to |
|---|---|---|---|
| Data owner | The business outcome the data supports, and the decision to change a definition. | estates role manager (planning, operations, energy, H&S, BIM) | estates director |
| Data steward | Day-to-day definitions, quality expectations and answering questions from users. | team leader or analyst working with the owner | data owner |
| Data custodian | The technical pipeline: loading, tests, documentation and access control. | data engineer or analytics colleague | estates analytics lead |
| Data consumer | Using the data honestly, quoting definitions and reporting problems found. | anyone using a dashboard, report or extract | data steward for the domain |

## Space and estate planning

Accountable owner: `estates-planning`. Steward: `estates-analytics`. Custodian: `estates-analytics`.

| Activity | Owner | Steward | Custodian | Consumer |
|---|---|---|---|---|
| Define what counts as a room and its net internal area | A | R | C | I |
| Approve a change to a space record (merge, split, re-code) | A | C | R | I |
| Publish space utilisation metrics | A | R | R | C |
| Decide the utilisation target used for release scenarios | A | C | I | C |

**Decision rights**

- Space definitions and area rules are the owner's decision on the steward's advice.
- The analytics lead may not change a published metric definition alone; that is an owner decision.
- Targets and thresholds are policy choices by the owner, not analytics choices.

**Escalation path**

- Disputed area or room count -> steward -> owner -> estates director if unresolved in 10 working days.
- A dashboard number that disagrees with a room sheet -> steward, then custodian for a data fix.

## Assets and maintenance

Accountable owner: `estates-operations`. Steward: `estates-analytics`. Custodian: `estates-analytics`.

| Activity | Owner | Steward | Custodian | Consumer |
|---|---|---|---|---|
| Maintain the asset register and criticality ratings | A | C | R | I |
| Set SLA targets by priority | A | C | I | I |
| Define expected design life per asset type | A | R | C | I |
| Publish MTTR, PPM completion and backlog measures | A | R | R | C |
| Decide when a data point needs contractor verification | A | R | C | C |

**Decision rights**

- Priority and SLA settings belong to operations; analytics cannot change them to improve a score.
- Expected life values are engineering judgements recorded in the register, with the owner accountable.
- Risk bands are conventions; changing them is an owner decision recorded in the change log.

**Escalation path**

- Condition data looks wrong for a specific asset -> steward -> operations manager.
- Missing or duplicated assets blocking a renewal plan -> steward -> custodian as an error-severity data issue.

## Energy and carbon

Accountable owner: `estates-energy`. Steward: `estates-analytics`. Custodian: `estates-analytics`.

| Activity | Owner | Steward | Custodian | Consumer |
|---|---|---|---|---|
| Adopt emission factors and their vintage | A | R | C | I |
| Choose location-based or market-based reporting | A | C | I | I |
| Publish carbon and intensity metrics | A | R | R | C |
| Approve the net zero baseline and target year | A | C | I | C |

**Decision rights**

- Factors are fetched from the official source each year; the owner approves adopting them.
- Any external claim (public reporting, funder returns) is an owner decision, not a pipeline default.
- Baseline and target years are parameters with an owner decision recorded in the change log.

**Escalation path**

- Meter outage or suspicious readings -> custodian as a data incident, then energy manager.
- A factor change that moves the carbon number by more than 1% -> steward notifies the owner before publishing.

## Compliance and safety

Accountable owner: `estates-hs`. Steward: `estates-analytics`. Custodian: `estates-analytics`.

| Activity | Owner | Steward | Custodian | Consumer |
|---|---|---|---|---|
| Maintain inspection frequencies in the register | A | I | R | I |
| Record remediation of a failed inspection | A | C | C | I |
| Publish the compliance status view | A | R | R | C |
| Escalate a failed inspection with no remedial action | A | R | I | I |

**Decision rights**

- Frequencies are legally driven; this repository encodes illustrative values only and the owner must confirm every real one.
- {'Nothing in the pipeline may mark an inspection compliant': 'only a recorded completion can.'}
- Publication can be paused by the owner for safety, with the reason logged.

**Escalation path**

- Failed inspection with an open action over 90 days -> owner -> estates director (as the P09 page 4 path describes).
- Suspected data loss in inspection records -> custodian immediately, error-severity incident.

## BIM, projects and information handover

Accountable owner: `estates-bim`. Steward: `estates-analytics`. Custodian: `estates-analytics`.

| Activity | Owner | Steward | Custodian | Consumer |
|---|---|---|---|---|
| Maintain the asset information requirements (AIR) template | A | C | I | I |
| Validate a project handover against the AIR | A | R | C | I |
| Enforce information naming and container conventions | A | C | R | I |
| Accept register records from a completed project | A | C | C | I |

**Decision rights**

- {'The AIR is a contractual instrument': 'the owner signs it, the custodian checks compliance with it.'}
- Classification code lists are adopted or not adopted by the owner; a placeholder is never silently promoted.
- Handover acceptance is the owner's decision even when the automated checks pass.

**Escalation path**

- Project deliverable missing an AIR item -> project manager first, then owner.
- Check results and register disagree after handover -> steward -> custodian for identity and crosswalk work (see P18).

## Decision rights that apply everywhere

- {'Who can change a definition': "only the accountable owner for that domain, on the steward's advice, recorded in the metric change log."}
- {'Who can change a threshold or target': 'the accountable owner. Analytics proposes; it does not decide.'}
- {'Who can publish': "the analytics lead on the owner's approval, once CI is green."}
- {'Who can change data classification': 'the owner, with the data protection contact consulted (awareness-level advice here, not legal advice).'}
- {'What breaks CI': 'any error-severity data quality failure, a stale generated page, a broken link, or a registry mismatch.'}

All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any real university, building or estate, and nothing here is a compliance statement.
