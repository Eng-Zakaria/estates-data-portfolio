# ADR and decision index

*All data referenced here is synthetic: no real estate, building, person or compliance status is described.*

Architecture decision records are short documents: the context, the choice, and what it costs you. This page indexes the ones in this repository and the decisions that were made inside the governance pack.

The full ADR text lives in the repository's `docs/adr/` folder. This page says what each decision was for and where to look for the trade-off.

## Records in the repository

| ADR | Decision | Why it was needed |
|---|---|---|
| `001-python-packaging.md` | single project with editable extras, shared packages under `packages/` | one dependency set for the platform and all twenty projects, without twenty virtual environments |
| `002-orchestrator-choice.md` | Airflow as the orchestrator, with tasks that are also runnable by hand | the pipeline must be operable when nobody is watching, but debuggable when someone is |

## Decisions made inside this pack

These are recorded here rather than as new ADR files because they are documentation decisions, not architecture decisions. The test suite enforces the parts that can fail silently.

| Decision | Choice | Why | Cost |
|---|---|---|---|
| Where the dictionary comes from | the dbt YAML and model SQL, with a compiled manifest used when one exists | a committed manifest is a build artefact that drifts; the YAML is reviewed in pull requests | column descriptions depend on the dbt project being written well |
| How dashboard KPIs are found | parse `measures.dax` and `src/kpis.py` in the dashboard projects | the registry follows the code that publishes numbers, instead of a list maintained by hand | a new dashboard must be added to the scan scope, and a test forces that decision |
| What "and vice versa" means | every entry names a consumer, or is marked planned with a reason | a registry full of unused definitions is a museum | some useful-but-unpublished metrics are marked planned instead of live |
| Cross-project links | written as code spans, not links | `mkdocs build --strict` fails on links outside the site, and a broken link is worse than a path in prose | readers of the published site must find the repository for those paths |
| External links | counted, never fetched | CI must not depend on the network | a dead external link is only found by a human |
| Readability gate | Flesch reading ease on the plain-English guides only, tables and code stripped | the guides are read by non-specialists; the dictionary is not prose | the number is a rough measure, so the measured values are published rather than hidden |
| DQ scores in the glossary | joined from the latest run, and "not measured" when absent | a definition without a quality score invites over-trust | pages change when a run changes, which is why staleness is a gate |
| Standards status vocabulary | implemented, mock, awareness-only, not-obtained | stops a placeholder from being read as a real mapping | the register needs updating when a standard is obtained |

## How to write an ADR here

1. One page: context, decision, consequences, and what would make you change it.
2. Name the alternatives you rejected and why, in one line each.
3. No diagrams that need a renderer the reader may not have.
4. Put the trade-off in writing. A decision with no recorded cost has not been thought about.

## Related documents

| Question | Document |
|---|---|
| who decides what | [governance framework](governance/framework.md) |
| naming, layers, identifiers, time zones | [naming and modelling standards](data/naming-standards.md) |
| what we can claim about standards | [standards register](generated/standards-register.md) |
| what to do when it breaks | [runbooks](runbooks.md) |
| what each project is and where its evidence is | [reference index](reference-index.md) |
