# SPEC (copy): P20 Governance and data-literacy pack

> Verbatim copy of the P20 section of `docs/specs/05-twin-spatial-governance-p18-p20.md`,
> kept in the project folder for traceability (AGENTS.md layout rule).

**Location:** `projects/p20-governance-literacy/` (MkDocs Material site published to GitHub Pages)
**Criteria:** E7, plus responsibilities: "Promote good practice in data governance, documentation, and repeatable workflows" and "Support training and engagement activities to improve data literacy"
**Stack:** MkDocs Material, mkdocs-mermaid plugin, Python scripts that generate pages from dbt `manifest.json`/`catalog.json`, data contracts and DQ results, textstat (readability), pytest, a link checker.

## Content (each item a short, usable page, not boilerplate)

1. **Governance framework:** principles; roles (owner, steward, custodian, consumer); RACI per domain (space, assets, energy/carbon, compliance, BIM); decision rights; escalation path.
2. **Data dictionary and business glossary:** auto-generated columns and tables from dbt/contracts; hand-written glossary for GIA, NIA, FTE, PPM, reactive, MTTR, utilisation, Scope 1/2, baseload, COBie, AIR, etc. Each entry: definition, owner, source of truth, refresh frequency, current DQ score.
3. **Metric registry** (`metrics.yml`): id, name, definition, formula, grain, owner, source model, caveats, version. **Test:** every KPI named in P06-P10 dashboards and `measures.dax` files exists in the registry, and vice versa.
4. **Data classification and handling:** public / internal / confidential; where personal data could appear in estates data (for example names on work orders) and how it is handled; UK GDPR awareness note (state it is not legal advice).
5. **Data quality policy:** link to P03 (dimensions, thresholds, severity, response times).
6. **Naming and modelling standards:** tables, columns, IDs, units, time zones (UTC storage, UK display).
7. **Standards register:** ISO 19650, Uniclass, COBie, SFG20, HESA EMR/TRAC, GHG Protocol: what each is, where it touches the data, owner, and **honest status** (implemented / mock / awareness-only).
8. **Information handover guide:** project → operations checklist linking P12/P14, AIR template, roles.
9. **Data request and change process:** intake form template, triage criteria, SLA, metric-change log.
10. **"How to read our dashboards" guide:** one page per dashboard (P06-P10, DQ scorecard): the question it answers, how to read each visual, common misreadings, definitions, refresh time, limitations, who to ask. Plain English.
11. **Training kit:** 10-minute demo script; 45-minute "Data literacy for Estates" workshop (learning outcomes, three exercises using the synthetic dashboards, answer key, 10-question quiz, feedback form); slide outline only (the human builds the slides); facilitator notes.
12. **Runbooks and ADR index** linking to the other projects' docs.

## Automation

Scripts regenerate dictionary, lineage and DQ-score pages from artefacts; CI fails if generated pages are stale, links are broken, or the metric-registry test fails.

## Acceptance

- `mkdocs build --strict` passes; link checker clean.
- Glossary and metric registry cover 100% of dashboard KPIs (test).
- Literacy guide readability measured (target Flesch reading ease ≥ 50); numbers reported, not hidden.
- Workshop pack is complete enough that someone else could deliver it from the folder alone.