# PLAN: P13 Uniclass classification mapper

## Goal
Assign Uniclass 2015 classification codes to messy free-text asset descriptions with confidence scores and a human review loop.

## Why P13 now
Next free item. Depends on P12 (COBie) for reference data sharing. Fresh `projects/p13-uniclass-mapper/` tree.

## Key constraints (hard rules)
- **Reference data**: Must use official Uniclass 2015 tables (Products `Pr_` and Systems `Ss_`) from NBS. Download URL: https://uniclass.thenbs.com/download (requires login/JavaScript; direct download not easily automated).
- **If download fails**: Use `mock_uniclass_dev_placeholder.csv` (loudly labelled non-authoritative) and refuse final outputs. Record gap in `docs/OPEN_QUESTIONS.md`.
- **Golden set**: ≥ 300 labelled examples (messy description → true code). Human must review ≥ 20% random sample (`review_sample.csv`) before reporting accuracy.
- **Methods**: 1) fuzzy (rapidfuzz token-set), 2) embedding retrieval (sentence-transformers), 3) hybrid (weighted fuzzy + embedding + keyword sub-tree filter), 4) optional LLM re-ranker (off by default).
- **Confidence policy**: auto-accept ≥ τ_high, review τ_low–τ_high, reject below. Choose on dev set for ≥ 95% precision on auto-accepts.
- **Streamlit review UI**: accept/override/note → saves to `human_decisions` → feeds `synonyms.csv` (active learning loop).
- **Metrics**: top-1/3 accuracy, precision/recall of auto-accept, confusion pairs, calibration plot, error analysis.

## Tasks
1. `scripts/fetch_uniclass.py`: Attempt download from https://uniclass.thenbs.com/download; on failure write `mock_uniclass_dev_placeholder.csv` (labelled non-authoritative) and log gap.
2. `src/reference.py`: Load Uniclass tables (Pr_, Ss_) with code, title, level, parent_code.
3. `src/normaliser.py`: Text normalisation (lowercase, abbreviation expansion dict, tokenisation, stop-words).
4. `src/fuzzy_matcher.py`: rapidfuzz token-set ratio against code titles + synonyms.
4. `src/embedder.py`: sentence-transformers (small model, e.g., all-MiniLM-L6-v2) for embedding retrieval (top-k cosine).
5. `src/hybrid.py`: Hybrid score = w1*fuzzy + w2*embedding + w3*keyword_rule (sub-tree filter).
6. `src/golden_set.py`: Build ≥ 300 labelled examples (asset descriptions × true codes). Generate `review_sample.csv` for human review.
7. `src/pipeline.py`: Orchestrate normalise → fuzzy → embed → hybrid → confidence bands → output.
8. `src/review_ui.py`: Streamlit UI (accept/override/note → human_decisions → synonyms.csv active learning).
9. `src/eval.py`: top-1/3 accuracy, precision/recall of auto-accept, confusion pairs, calibration plot.
9. `tests/`: normaliser unit tests, fuzzy/embedding fixture tests, golden set accuracy tests.
10. `docs/OPEN_QUESTIONS.md`: Record Uniclass download gap.
10. `make p13-run`, `README.md`, `SPEC.md`, `STATUS.md`, `DATA.md`.

## Risks
- Uniclass download requires NBS login; direct scripted download may not work. → mock placeholder + documented gap.
- sentence-transformers model download on first run; cache in `data/reference/`.
- Golden set labelling requires human time; generate synthetic first, then human reviews sample.
- Threshold tuning on dev set only; never tune on test.

## Open questions
- Official Uniclass download URL + authentication method (record in OPEN_QUESTIONS.md).
- sentence-transformers model choice and licence (all-MiniLM-L6-v2 is Apache 2.0).
- Uniclass 2015 table version/date (record in DATA.md).
- Sub-tree filter logic: use parent_code hierarchy from Uniclass.