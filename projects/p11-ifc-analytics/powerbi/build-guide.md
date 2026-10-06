# P11 Power BI build guide

1. Create `GoldFolder` parameter (Text) = absolute path to `data/gold/ifc`.
2. Get Data → Parquet → import each `queries/*.pq` as a new query (one per table + `recon_model_vs_register`).
3. Import `qa_report.csv` for the standards table on page 1.
4. Build relationships per `model.md`; mark GlobalId columns hidden; set `area_delta_pct` format to 0.0%.
5. Add measures from `measures.dax` (one at a time; check each against validation below).
6. Build pages per `wireframe.md`; apply `theme.json` via View → Themes → Browse for themes.
7. Add a footer text box: "Synthetic data for portfolio demonstration — no real building performance implied."

## Validation checklist (tie back to SQL/CSV)

| Check | Power BI value | Source of truth |
|---|---|---|
| Space Count | 32 | `qa_report.csv` → counts.spaces |
| Element Count | 5 | `qa_report.csv` → counts.elements |
| Zero Area Spaces | 1 | `qa_report.csv` → zero_area_spaces |
| Elements Without Type | 5 | `qa_report.csv` → elements_without_type |
| Elements Without Classification | 3 | `qa_report.csv` → elements_without_classification |
| Rooms Matched | 31 | `recon_summary_by_building.csv` |
| Rooms Missing From Model | ≥5 (planted) | `recon_model_vs_register.parquet` |
| Over-10% area mismatch | ≥12 (planted) | same, filtered ABS(area_delta_pct) > 0.10 |

Reconciliation cross-check (DuckDB):

```sql
SELECT status, COUNT(*) FROM read_parquet('data/gold/ifc/recon_model_vs_register.parquet') GROUP BY 1;
```
