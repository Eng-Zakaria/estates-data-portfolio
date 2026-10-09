# Estates data governance and literacy pack

**Synthetic portfolio.** Every number, building and person in this pack comes from a data generator. Nothing here describes a real university estate, and nothing here is a compliance statement.

## What this is for

Estate data is spread across systems: a space register, a maintenance system, meter files, sensor feeds, BIM models and spreadsheets kept by teams. This pack is the shared set of answers that stops it going wrong:

- who owns each piece of data, and who may change its meaning;
- what every published number actually measures;
- how each piece of data is classified and handled;
- which standards we follow, and honestly, how far we have got;
- how to read each dashboard without being misled;
- how to ask for data or for a change, and what happens next;
- a 45-minute training pack so other people can use all of the above.

## Where to start

| If you want to... | Read |
|---|---|
| know who decides what | [Governance framework](governance/framework.md) |
| look up a word or a number | [Data dictionary](data/dictionary.md) and [business glossary](data/glossary.md) |
| check a KPI is registered | [Metric registry](generated/metric-registry.md) |
| see how good the data is | [Data quality scores](generated/dq-scores.md) |
| see where a table comes from | [Lineage](generated/lineage.md) |
| know what we can and cannot claim | [Standards register](generated/standards-register.md) |
| use a dashboard | [How to read our dashboards](dashboards/index.md) |
| ask for data or a change | [Data request and change process](process/data-request.md) |
| hand over a project | [Information handover guide](standards/handover.md) |
| run a training session | [Training kit](training/workshop.md) |
| follow an incident | [Runbooks](runbooks.md) |

## How this pack is built

The YAML files at the top of this folder are the source of truth: `metrics.yml`, `glossary.yml`, `raci.yml` and `standards.yml`. The pages under `generated/` are rendered from them and from the repository's dbt project and data quality output.

Two tests keep the two halves honest:

1. every KPI a dashboard publishes must exist in `metrics.yml` and in the glossary, and every registry entry must name who uses it;
2. the generated pages must match a fresh build, and every in-site link must resolve.

CI fails when either is untrue, so the documentation cannot quietly fall behind the dashboards.

## Reading the numbers

| Table | What it shows |
|---|---|
| [Dictionary](generated/data-dictionary.md) | every table and column in the analytics layer, with descriptions and tests |
| [Lineage](generated/lineage.md) | which table reads which, and what the dashboards read |
| [DQ scores](generated/dq-scores.md) | measured quality scores by dataset, dimension and failing check |
| [Glossary](generated/glossary.md) | plain-English definitions with owner, source, refresh and current DQ score |
| [Metric registry](generated/metric-registry.md) | every published KPI with formula, grain, owner, version and caveats |
| [Standards register](generated/standards-register.md) | each standard, where it touches the data, and its honest status |
| [RACI](generated/raci.md) | who is responsible, accountable, consulted and informed, per domain |

## Honest limits

- The data is synthetic, so the scores and volumes are examples, not benchmarks.
- The roles, owners and service levels in this pack are a proposal. A real institution ratifies them with named people and a data protection contact.
- Standards are recorded with their real status: implemented, mock, awareness only, or not obtained. Nothing is claimed that has not been verified.
- Where this pack says "not legal advice", that is deliberate. Data protection and statutory duties need qualified advice.

Start with the [governance framework](governance/framework.md), then use the [training kit](training/workshop.md) to walk colleagues through it.