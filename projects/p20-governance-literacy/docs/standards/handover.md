# Information handover guide: project to operations

A building is handed over twice: once with keys, and once with information. The second handover is the one estates inherits, often long after the project team has gone. This checklist is the version used by this portfolio: a generic AIR (Asset Information Requirements) list plus the checks that can be automated.

A real estate keeps one organisation-level AIR template and per-project addenda. What follows is a portfolio-level draft.

## Who is involved

| Role | At handover they... |
|---|---|
| Owner (BIM) | accept or reject the handover; accountable for the decision |
| Project manager | chase the missing items, with the contract as lever |
| Custodian (analytics) | run the checks, load the data, rebuild the crosswalk |
| Steward (operations) | confirm the register matches what is in the building |
| Operations team | take over the assets, spares, manuals and training |

## The checklist

### 1. Information requirements agreed before design

- [ ] The AIR names the datasets to be delivered, the format, the owner and the date.
- [ ] Naming conventions follow the agreed standard (see [naming standards](../data/naming-standards.md)); deviations are listed and agreed.
- [ ] Every asset that will need a record in the estate register has a stable identifier assigned at design stage, not invented at handover.
- [ ] The AIR states who may publish data and at what classification.

### 2. Model and data quality

- [ ] The model passes the information checks: container states, statuses and identifier format.
- [ ] Every space in the model maps to a room in the space register, or the difference is explained.
- [ ] Every element has a type and a classification, or a recorded reason why not.
- [ ] Areas reconcile with the register within an agreed tolerance, with differences listed.
- [ ] Classification uses the agreed code list. A placeholder classifier is not acceptable for acceptance.

### 3. Handover pack contents

- [ ] Asset register extract with stable ids, type, location, and expected life.
- [ ] Equipment list with make, model, serial, warranty and maintenance schedule.
- [ ] O&M manuals and drawings, as documents in the CDE, not as links to a project laptop.
- [ ] Test and commissioning records, with the as-built values rather than the design values.
- [ ] Spares list and quantities, with a location.
- [ ] Controls and BMS points list, with point identifiers that match what the BMS reports.
- [ ] Statutory inspection schedule for the new assets, with the responsible owner.
- [ ] Training delivered and attendance recorded.
- [ ] Health and safety file, asbestos register updates, and fire strategy updates where relevant.

### 4. Register and data update

- [ ] New and changed assets loaded into the asset register with their stable ids.
- [ ] Spaces added or retired in the space register, with the effective date.
- [ ] Meters registered, with utility, role and the building they serve.
- [ ] The digital twin crosswalk rebuilt so the new ids resolve to their native system ids.
- [ ] Sensor points registered where the building has them.
- [ ] Reconciliation run: nothing lost between source and register. Discrepancies listed and owned.

### 5. Acceptance

- [ ] Automated checks rerun after loading; results attached to the handover record.
- [ ] Operations confirm the register matches what is physically there, for a sample plus every critical asset.
- [ ] Open items list with owners and dates; nothing silently dropped.
- [ ] Owner records the acceptance decision and the date, with the outstanding items named.

## What automation can and cannot do

| Check | Automated here | Still needs a person |
|---|---|---|
| Container states, statuses, identifier format | yes | deciding whether an exception is acceptable |
| Room matching between model and register | yes | confirming a fuzzy match that looks right |
| Area differences above a tolerance | yes | deciding which number is correct |
| Element type and classification present | yes | judging whether the classification is sensible |
| Spares, manuals and training delivered | no | all of it |
| Register matches the physical estate | no | sampling and sign-off |

## Common failure modes

1. **Identifiers invented at handover.** If ids appear for the first time in the handover pack, nothing links back to design or commissioning. Assign them early.
2. **As-built never updated.** Design values reach operations and are wrong from day one.
3. **Names instead of ids.** Rooms are handed over as "Meeting Room 2B" with three similar rooms in the building.
4. **O&M documents in a project folder.** The project folder is deleted at contract completion; documents belong in the CDE.
5. **Sensors registered but never mapped.** A point exists in the BMS and nothing in the estate data, so the space looks unmonitored.
6. **Quiet acceptance of gaps.** "Accepted with minor comments" hides the two items that matter. List them.

## After acceptance

- Add the new assets to the maintenance plan with real intervals, not copy-pasted defaults.
- Add the spaces to utilisation reporting and check the first full term's numbers.
- Register inspection dates so compliance reporting includes them from the next run.
- Record what the project taught you as a change to the AIR template, so the next project starts better.