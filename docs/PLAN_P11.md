# PLAN: P11 IFC → analytics pipeline

## Goal
Convert IFC model files into queryable analytical tables (spaces, elements, types, systems, properties, quantities), run a model-QA report, and reconcile against the space register. No geometry processing.

## Tasks
1. Verify IfcOpenShell 0.9.0 API empirically: `ifcopenshell.open()`, entity iteration, `Qto_SpaceBaseQuantities`, property sets, systems. Record exact API in comments.
2. Scaffold `projects/p11-ifc-analytics/`: `src/ifc2tables/`, `tests/`, `README.md`, `SPEC.md` (copy of P11 section), `Makefile` targets.
3. `make_sample_ifc.py`: build synthetic IFC using IfcOpenShell API — project → site → building B003 → storeys → IfcSpace with Qto → distribution elements (AHU, boiler, pump, FCU) with classification, manufacturer/type psets, system membership. Plant defects: elements without type/classification/space, duplicate names, zero-area spaces, 12 rooms with area diff >10% from register, 5 rooms missing from model (match ground_truth.yaml).
4. `ifc2tables` CLI: `model.ifc --out data/gold/ifc/`. Outputs: ifc_project, ifc_storeys, ifc_spaces, ifc_elements, ifc_types, ifc_systems, ifc_system_members, ifc_properties_long, ifc_quantities_long, ifc_classifications. Stable key=GlobalId. Area from Qto with fallback flag. Incremental by file hash. Log runtime vs element count.
5. Model QA report (HTML + CSV): counts by class; missing classification/type/space/required psets; duplicate GlobalIds; zero/negative areas; spaces without storey; naming conformance; completeness % per pset.
6. Reconciliation: `recon_model_vs_register` — area delta per room, rooms in model not in register and vice versa, summary by building. 100% recall of planted mismatches/missing rooms.
7. Tests: tiny fixture IFC committed to repo; extraction correctness; QA report counts match generator log; reconciliation recall 100%; both IFC2X3 and IFC4 paths (document differences).
8. Power BI handoff spec: "Model data health" page + "Space & asset explorer" page (spec only, no .pbix).
9. Acceptance: all seeded defects in QA report; 100% recall of area mismatches/missing rooms; runtime table; works on public sample + synthetic model.

## Risks
- IfcOpenShell 0.9.0 API may differ from memory — verify by running, not by reading docs alone.
- IFC2X3 vs IFC4 schema differences — handle both, document encountered differences.
- Large models: no geometry, extraction should stay fast; document runtime vs element count.
- Licence of public sample IFC — check before committing; likely CC-BY or similar, record in DATA.md.

## Open questions
- Public sample IFC URL + licence — fetch and record in DATA.md or use synthetic only if licence unclear.
