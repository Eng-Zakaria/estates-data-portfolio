# P11 Power BI handoff — Model data health & Space/asset explorer

> Synthetic data for portfolio demonstration. No real building performance or compliance status is implied.

## Business questions (question → insight → decision)

- Are our models complete enough to trust? → QA report: 1 zero-area space, 5 elements without type, 3 without classification, 1 duplicate element name → raise model-authoring issues with the BIM team before relying on the data.
- Does the model agree with the space register? → 31 rooms matched, 5 missing from model, 12 with >10% area mismatch → prioritise register-vs-model audit for B003.
- Which entities lack classification/type? → elements_without_classification = 3, elements_without_type = 5 → completeness % per pset drives a classification backlog.

## Files

- `model.md` — tables, relationships, hidden fields.
- `queries/*.pq` — Power Query scripts loading Parquet from `data/gold/ifc` (parameterised `GoldFolder`).
- `measures.dax` — QA counts, completeness %, reconciliation recall.
- `wireframe.md` — page layouts for "Model data health" and "Space & asset explorer".
- `theme.json` — accessible theme consistent with other portfolio dashboards.
- `build-guide.md` — click-by-click steps plus validation checklist tied to `qa_report.csv` / reconciliation SQL.
