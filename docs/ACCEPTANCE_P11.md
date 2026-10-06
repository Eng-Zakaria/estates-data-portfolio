# ACCEPTANCE P11 — IFC → analytics pipeline (2026-10-06)

> Synthetic data throughout. No real building performance or compliance status implied.

## Delivered

| Area | Path | Notes |
|---|---|---|
| Spec copy | `projects/p11-ifc-analytics/SPEC.md` | Copied from `docs/specs/03-bim-standards-p11-p14.md` |
| Pipeline | `projects/p11-ifc-analytics/src/ifc2tables/` | `make_sample_ifc.py`, `extract.py`, `qa_report.py`, `reconcile.py`, `cli.py` |
| Tests | `projects/p11-ifc-analytics/tests/test_ifc2tables.py` | 6 passed; fixture IFC committed at `tests/fixtures/sample_b003.ifc` (18 KB) |
| Power BI handoff | `projects/p11-ifc-analytics/powerbi/` | model.md, 11 .pq queries, measures.dax, wireframe.md, theme.json, build-guide.md |
| Makefile | `p11-run` target | pytest + generate + extract + QA + reconcile |
| pyproject | `ifcopenshell==0.9.0` pinned | Added after env rebuild wiped the ad-hoc install |

## Acceptance mapping (spec bullets)

| Bullet | Evidence |
|---|---|
| All seeded model defects appear in the QA report | `data/gold/ifc/qa_report.csv`: zero_area_spaces=1, elements_without_type=5, elements_without_classification=3, duplicate_element_names=1, elements_without_system=2 — match generator planted counts (test `test_qa_report_counts`) |
| 100% recall of planted area mismatches / missing rooms | `reconcile.py` output: Missing from model: 5 B003 planted (+ other-building rooms outside scope), Area mismatch >10%: 12 — test `test_reconcile_recall` asserts ≥5 missing and ≥12 mismatches |
| No geometry processing; runtime documented | Extract of 32 spaces + 5 elements + 2 types + 3 systems: **0.49 s**, 10 Parquet tables written; README §5 documents the runtime-vs-element-count approach |
| Works on synthetic model; tests use committed fixture | `tests/fixtures/sample_b003.ifc` used by all 6 tests; public-sample path documented (no public sample committed — licence gate noted in README/DATA.md) |
| IFC2X3 and IFC4 differences documented | README/SPEC note: synthetic model is IFC4; IfcOpenShell 0.9.0 open path is schema-agnostic for the attributes read; IFC2X3 differences remain a documented hypothesis (see docs/OPEN_QUESTIONS.md) |

## Local verification

| Check | Result |
|---|---|
| `uv run pytest projects/p11-ifc-analytics/tests` | 6 passed |
| Extract runtime (32 spaces, 5 elements) | 0.49 s |
| Tables written | 10 (`ifc_project, ifc_storeys, ifc_spaces, ifc_elements, ifc_types, ifc_systems, ifc_system_members, ifc_properties_long, ifc_quantities_long, ifc_classifications`) |
| QA report | `qa_report.html` + `qa_report.csv` regenerated 2026-10-06 |
| Reconciliation | `recon_model_vs_register.parquet` + `recon_summary_by_building.csv`; 31 matched, 12 area mismatches |

## Deviations / open questions

- Public sample IFC not committed: licence unresolved at build time — use synthetic only; listed in docs/OPEN_QUESTIONS.md.
- `recon_model_vs_register` counts `missing_from_model` for rooms outside B003 (other campus buildings); the >10% mismatch recall is scoped to B003 where the model exists. Tests assert the planted B003 counts (≥5, ≥12).
- No `.pbix` produced (Power BI is GUI-only); handoff pack + validation SQL provided per AGENTS protocol.
