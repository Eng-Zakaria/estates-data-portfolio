# P05 pull request template (mirrors the CI gate + portfolio definition of done).

## What changed

## Checklist

- [ ] Tests added/updated; `pytest` passes locally
- [ ] Docs updated (README / `docs/`) for user-visible changes
- [ ] DQ impact assessed (new/changed checks? quarantine behaviour?)
- [ ] Data-contract change? (bronze/silver schemas, dbt contracts, seeds)
- [ ] Synthetic-data note kept on any new chart/table output
- [ ] No secrets, no large data/binaries committed (`git status` clean of `data/`, `*.parquet`)

> CI runs lint + type + tests + small-profile data → ingest → `dbt build` →
> DQ gate + terraform/docker/airflow/docs checks. A red CI blocks merge.
