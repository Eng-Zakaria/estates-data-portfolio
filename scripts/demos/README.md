# Interactive demo pages

`scripts/build_demos.py` generates one self-contained HTML page per portfolio
project into `docs/apps/`, which is served from the GitHub Pages site root.

```bash
make demos          # rebuild every page from the gold marts
make demos-serve    # http://localhost:8899 to browse them
```

## Design rules

1. **Every number is measured.** Pages read the same gold marts, DuckDB stores
   and project outputs that the READMEs and acceptance docs quote, so a
   reviewer can tie any figure back to a test or a validation query.
2. **Never invent a number.** If an input is missing the page says so
   ("`mart_compliance_status` not found — run `make dbt-build``) instead of
   showing an empty chart.
3. **Synthetic data is stated on every page**, in a banner, not buried.
4. **Honest caveats travel with the figures.** P13's placeholder Uniclass
   tables, P16's threshold that does not transfer across profiles, and P19's
   "footprint ≠ floor area" are all on the page, not only in the README.
5. **Static only.** No server, no framework. Plotly and Leaflet load from a CDN,
   which keeps the committed HTML at ~670 KB instead of tens of megabytes.

## Layout

| File | Purpose |
|---|---|
| `build_demos.py` | Entry point: collects builders, writes pages, writes `index.html` |
| `demos/base.py` | HTML template, Plotly figure helpers, KPI/table/note helpers |
| `demos/data.py` | Read-only loaders over gold marts, DuckDB stores, project outputs |
| `demos/catalogue.py` | The 20 projects: id, label, slug, one-line purpose |
| `demos/pages_platform.py` | F, P01–P05 |
| `demos/pages_dashboards.py` | P06–P10 |
| `demos/pages_bim.py` | P11–P15 |
| `demos/pages_analytics.py` | P16–P20 |

Each module exposes `PAGES = {slug: builder}`. A builder returns
`(picker, title, subtitle, body_html, extra_js)` and may append `extra_head`
for a CDN stylesheet or script.

## Adding a page

1. Add the project to `catalogue.PROJECTS` if it is new.
2. Write a builder in the matching `pages_*.py` and register it in that
   module's `PAGES` dict.
3. Return the five-item tuple; use `base.chart`, `base.kpi`, `base.table`,
   `base.note` for content.
4. Run `make demos` and open the page — check the console for errors.
5. If the data is optional, guard it and render a notice rather than failing.

## Why static HTML rather than Streamlit on Pages

GitHub Pages serves static files only. The portfolio keeps real Streamlit apps
for local use (`projects/pNN-*/streamlit_app.py`) and publishes static pages
for the public demo, so the site works without a Python runtime, without a
database and without a server — and every figure still ties back to the
pipeline that produced it.