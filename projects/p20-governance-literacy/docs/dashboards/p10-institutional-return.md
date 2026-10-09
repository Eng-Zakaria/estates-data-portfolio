# Institutional return

**Question it answers:** what goes into the monthly pack that the committee and the returns team see?

**Refresh:** on demand for a chosen date, so the same date always gives the same pack.

**Who to ask:** estates finance (the numbers in the pack); the analytics steward for the mapping.

!!! warning
    This pack is a mock. The field mapping was written for demonstration. It is not an official HESA or funder mapping, and the categories are illustrative. The [standards register](../generated/standards-register.md) records that status.

## What the pack contains

| File | What it holds | Why it is there |
|---|---|---|
| `return_<date>.xlsx` | the full pack, one sheet per section | what a committee receives |
| `return_pack_<date>.html` | the same pack as a single page | easy to read on screen |
| `building_areas_<date>.csv` | area by building | the denominators |
| `category_mapping.csv` | internal room types mapped to return categories | shows the judgement in the mapping |
| `cost_allocation_<date>.csv` | costs split by pool and activity | the allocation basis |
| `energy_<date>.csv`, `emissions_<date>.csv` | the energy and carbon section | links to the energy report |
| `costs_<date>.csv` | cost totals by building | ties back to the maintenance report |
| `validation_<date>.yaml` | the checks run and any violations | proof the pack is internally consistent |

## How to read it

- **Start with the validation file.** It lists the checks and any breaches. A clean file is a starting point, not a guarantee.
- **Read the mapping file before the numbers.** It shows which internal room types became which return category. If a mapping looks odd, every figure that depends on it is suspect.
- **Check the date stamp on every file.** The pack is built for one as-at date. Two packs with different dates should never be compared directly.
- **Allocation is a choice.** Costs are split by pool and activity using drivers such as floor area and staff numbers. The driver totals are in the file so the split can be checked.

## Common misreadings

1. **Allocated cost is not a measured cost.** It is a share of a pool, chosen by a driver.
2. **The categories are not official.** Mapping office space to a research activity is an illustration, not a rule.
3. **Areas are register values.** They come from the space register, so a register error moves every per-area figure.
4. **A pack is a snapshot.** It does not update until it is rebuilt. The date is not a refresh time.
5. **Totals across files must agree.** If they do not, the validation file should have said so. Report it.

## Limitations to say out loud

- The mapping has not been checked against an official specification.
- No confidence or estimation method is applied; figures are as recorded.
- Emissions come from the synthetic energy tables, so they move with the factors.
- The pack is generated, not published to a system. There is no audit trail beyond the files themselves.

## Definitions and versions

The measures used are registered in the [metric registry](../generated/metric-registry.md). Terms such as gross internal area and FTE are in the [business glossary](../generated/glossary.md).

## State of this project

In this checkout the pack's output files are present under the repository's generated data folder, but the project's source code, README and acceptance record are not. Treat this page as a description of the pack's shape and content, and verify the outputs against the files rather than against this text. That gap is recorded in the repository's status table.