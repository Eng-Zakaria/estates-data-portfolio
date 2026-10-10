# Assets and maintenance

*All data referenced here is synthetic: no real estate, building, person or compliance status is described.*

**Question it answers:** is planned work keeping up with breakdowns, what is ageing, and what will we have to replace soon?

**Refresh:** daily, from the maintenance system. The reports are built from five saved queries so the numbers can be checked by hand.

**Who to ask:** estates operations (priorities, intervals, contractors); the analytics steward for definitions.

## The five views

| View | What it shows | Read it when |
|---|---|---|
| 1. Overview | job counts by type, PPM completion, planned to reactive, time to repair, total cost | you want the shape of the workload |
| 2. Backlog and response times | open jobs by age band, and whether each priority met its target | you are asked "are we keeping up?" |
| 3. Reliability | repeat failures, failures by building and type, time between failures | you suspect a plant or contractor problem |
| 4. Lifecycle | condition mix, assets past expected life, replacement forecast, cost per square metre | you are planning capital |
| 5. Planted checks | checks against the faults deliberately put in the demo data | you are testing whether a check works |

## How to read each measure

- **PPM completion %** is planned jobs finished divided by planned jobs due. It measures closure, not quality: a job closed with no evidence still counts.
- **Planned to reactive ratio** is planned, statutory and project jobs divided by breakdown jobs. Above one means most work was scheduled. It can also mean breakdowns are not being recorded.
- **Time to repair** is the average days from raising a breakdown job to closing it. Open jobs are left out, so a growing backlog does not show here.
- **Time between failures** needs at least two failures on the same asset. Most assets are left out, which is worth knowing.
- **Repeat failure flag** marks assets with three or more breakdown jobs in twelve months. It counts jobs, not causes, so one fault fixed four times looks like four faults.
- **Remaining life %** is share of design life still to run. It goes negative past that life, and we report it as it is.
- **Renewal forecast** sums replacement cost by year. Assets with no install date are left out, so it is a floor, not a total.
- **Cost per square metre** uses whole-building floor area, not usable area, and covers job costs only.

## Common misreadings

1. **A good response-time rate can hide a bad backlog.** Completed jobs are counted; open ones are not.
2. **A high planned ratio is not always good.** It can mean under-reporting of breakdowns.
3. **Repeat failures are job counts.** The cause may be one fault, one part or one contractor.
4. **Targets here are examples, not contracts.** They are set in the project's method note so the maths is visible, not taken from a contract.
5. **Cost per square metre here does not match the space report.** One uses whole-building area, the other usable area. Never put them in the same table.
6. **Age bands are a convenience.** They are fixed bands of days, not a risk judgement.

## What the demo data shows

On the small profile: PPM completion is high, the ratio of planned to breakdown work is close to two, and average repair time is a little over three days. About 170 assets carry the repeat-failure flag. Condition grades are spread across all four bands, and roughly 370 assets are past their expected life. These numbers are examples produced by the generator. They are not a benchmark and they describe no real estate.

## Limitations to say out loud

- Maintenance records are what the system was told, not what was done.
- Expected design life is one number per asset type and ignores condition surveys.
- The renewal forecast has no inflation and no quotations behind it.
- Contractor names are there to filter by, not to build a league table.

## Definitions and versions

Formulas, owners, versions and caveats are in the [metric registry](../generated/metric-registry.md). Words such as PPM, reactive and MTTR are in the [business glossary](../generated/glossary.md).
