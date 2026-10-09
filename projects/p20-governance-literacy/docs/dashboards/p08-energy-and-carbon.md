# Energy and carbon

**Question it answers:** where do our emissions come from, which buildings drive them, and are we on the path we said we would be?

**Refresh:** monthly, from half-hourly meter files. Emissions use the government's conversion factors for that year, fetched by script.

**Who to ask:** estates energy (factors, baseline, target year); the analytics steward for definitions.

## The five pages

| Page | What it shows | Read it when |
|---|---|---|
| 1. Pathway and cards | total energy, scope 1, scope 2, intensity, gap to the pathway line | a committee or funder asks where we stand |
| 2. Building league table | every building ranked by emissions per square metre | you want to know who to visit |
| 3. Energy profile | daily use and an hour-by-day heat map | you are chasing a specific building |
| 4. Out-of-hours waste | baseload share by building, plus summer gas use | you want the quick wins |
| 5. Scenario planner | sliders for setpoint, baseload and grid factor, with the effect shown | you are testing an idea before costing it |

Slicers: building, fuel, month. Page 1 also shows heating degree days, which explain most month-to-month swings.

## How to read each measure

- **Total energy** is metered kilowatt hours. Gas and electricity kWh are both energy, but not comparable amounts of demand.
- **Scope 1** is gas burned on site. **Scope 2** is emissions from bought electricity, counted the location way.
- **Emissions intensity** is emissions per square metre of whole-building area. A small old building can out-rank a large efficient one.
- **Variance to pathway** compares actual emissions with a straight line from the base year to the target year. The line is a planning choice, not an official path.
- **Rolling 12-month total** smooths the season. Skip the first eleven months: they are part years.
- **Baseload %** is the average overnight low compared with the average daily peak. A high share means the building never really shuts down.

## Common misreadings

1. **These are location-based numbers.** No green tariff or certificate is claimed. A market-based figure would be lower and needs contractual evidence we do not hold.
2. **Factors change every year.** When the new factor set arrives, last year's number is restated. Compare like-for-like versions.
3. **Intensity uses whole-building area.** A building with missing area is dropped from the ratio but still counted in the total. The two never agree.
4. **A cold month looks like a failure.** Check the degree days line before drawing a conclusion.
5. **Baseload is not automatically waste.** Server rooms, labs and hot water plant are meant to run.
6. **The pathway line is a parameter.** Change the base year or the target year and the gap changes shape.
7. **The planner is a calculator, not a forecast.** Sliders show arithmetic. They do not include cost, plant limits or control changes.

## What the demo data shows

On the small profile, gas and electricity both matter, with the oldest plant buildings high on emissions per square metre, and one building with a large overnight baseload. The summer gas table is empty on the short profile because the window does not cover June to August. These are examples from the generator.

## Limitations to say out loud

- Emissions come from metered fuel only. An unmetered burner is missing, not zero.
- No weather correction is applied beyond showing degree days.
- No market-based accounting and no offset claims.
- Building areas come from the space register, not from measured plans.

## Definitions and versions

Formulas, owners, factor years and caveats are in the [metric registry](../generated/metric-registry.md). Words such as scope 1, baseload and degree day are in the [business glossary](../generated/glossary.md). The factor source and licence are recorded in the repository's `DATA.md`.