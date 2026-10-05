# Estates Data Portfolio (synthetic)

> **All data in this portfolio is synthetic or from public open sources. No real
> university, building performance, or compliance status is implied.**

A portfolio of 20 data projects demonstrating University Estates Data Analyst
skills: pipelines, space/asset/meter integration, Power BI reporting, data
quality, standards and sustainability reporting.

## Project status

See `STATUS.md` in the repo root. Foundation (campus generator), P01 (lakehouse)
and P05 (CI/CD) are done; P04 (dbt marts) models build green with docs and
acceptance still to land.

## CI/CD (P05)

Every PR runs lint + type + tests + small-profile data → ingest → `dbt build` →
DQ gate, plus terraform/docker/docs checks (`.github/workflows/ci.yml`). See
[CI demo](ci-demo.md) and [P05 acceptance](ACCEPTANCE_P05.md).
