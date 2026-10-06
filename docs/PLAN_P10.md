# PLAN: P10 Mock institutional return (HESA EMR / TRAC-style)

## Goal
Mock institutional return showing estates data → validated, reconciled,
auditable return + TRAC-style cost allocation. Full audit trail.

## Why P10 now
Next free item. Dependencies stable: space/building/energy marts green.
Fresh `projects/p10-institutional-return/` tree.

## Key facts (measured 2026-10-05, small profile seed 42)
- 8 buildings (B001–B008), 495 spaces, 6 departments.
- Space categories: Teaching (135), Office (118), Residential (64), Lab (62),
  Library (42), Support (39), Sports (21), Catering (14).
- Energy: Scope 1 (gas) 258,943 kWh, Scope 2 (elec) 609,043 kWh.
- Water/heat not in HH feeds; will be noted as not available (NA).
- Cost pools: rates, utilities, maintenance, cleaning, security (synthetic
  from work orders + rates proxy).

## Tasks
1. `docs/SOURCES.md`: HESA EMR coding manual URL (public), TRAC guidance
   URL (public), retrieval dates. Where not accessible → generic categories,
   marked illustrative, gap in OPEN_QUESTIONS.md.
2. `src/mapping.py`: internal → return category map (versioned config;
   test: every internal maps exactly once).
3. `src/return_builder.py`: building-level areas by return category
   (GIA/NIA), energy by fuel, emissions, water (NA), other sections.
   Output: Excel (openpyxl), CSV, HTML pack.
4. `src/validation.py`: YAML rules (completeness, valid codes,
   arithmetic, energy reconciliation ± tolerance, YoY >±15% flag,
   cross-field). Severity: blocking vs query. Output validation report.
5. `src/cost_allocation.py`: TRAC-style pools (rates, utilities,
   maintenance, cleaning, security) → Teaching/Research/Other via
   NIA × category weighting × department activity split. Checks:
   allocated = pool total, no negatives.
6. `src/audit.py`: run_log (run_id, git sha, config hash, input hashes,
   rule-set version, timestamp), sign_off, immutable snapshots (Parquet
   + SHA256), deterministic re-run test.
7. `tests/`: seeded errors (area mismatch, wrong code, energy mismatch,
   missing building) caught with correct severity; deterministic hash
   test; cost allocation sum test.
8. `powerbi/`: optional one-pager (blocking/query counts, reconciliation
   differences) — model.md, queries, measures, wireframe, build-guide.
9. `README.md` (9-section), `SPEC.md`, `make p10-run`, STATUS.md,
   commit.

## Risks
- HESA/TRAC public docs may be behind login/gates → use generic
  categories, mark illustrative, list gaps.
- TRAC cost driver methodology is complex; use documented simplification
  (NIA × category weight × dept activity split).
- Water/heat not in data → NA in return, documented.

## Open questions
- HESA EMR public spec URL (need to fetch/verify).
- TRAC guidance public URL (need to fetch/verify).
- Exact return category code list (use generic "Teaching", "Research",
  "Other", "Residential", "Commercial" with mapping table).