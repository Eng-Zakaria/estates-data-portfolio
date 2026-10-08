# P13 SPEC (copy of docs/specs section — traceability)

## P13: Uniclass classification mapper

**Location:** `projects/p13-uniclass-mapper/`
**Criteria:** E6, D6 (also supports P12)
**Stack:** Python, rapidfuzz, sentence-transformers (small embedding model; verify availability and licence), scikit-learn, numpy/FAISS, Streamlit, DuckDB, pytest.
**Goal:** assign classification codes to messy free-text asset descriptions with confidence scores and a human review loop.

### Reference data (hard rule)
Download the **official Uniclass 2015** tables from NBS (at least Products `Pr` and Systems `Ss`; check the terms of use; record version/date in `DATA.md`). **Never invent codes.** If the download is not possible, stop and note it in `docs/OPEN_QUESTIONS.md`; for development use `mock_uniclass_dev_placeholder.csv`, loudly labelled non-authoritative, and make the pipeline refuse to produce "final" outputs from it.

### Golden set
Build ≥ 300 labelled examples: messy descriptions ("AHU-03 air hndlg unit L2", "Boiler no 2 (Remeha)", "FCU fan coil rm 214", "emerg lighting luminaire"...) × true codes. Foundation provides the asset types; the agent drafts labels against the *official* table; **the human must review a ≥ 20% random sample** (generate `review_sample.csv` for this) before reporting accuracy. Split train/dev/test once; never tune on test.

### Methods (compare all)
1. Text normalisation: lowercase, abbreviation expansion dictionary (AHU, FCU, VAV, PRV, MCC, UPS, etc.), tokenisation, stop-words.
2. Baseline fuzzy matching (`rapidfuzz` token-set ratio) against code titles + synonyms.
3. Embedding retrieval (top-k cosine).
4. Hybrid score (weighted fuzzy + embedding + keyword-rule sub-tree filter).
5. Optional LLM re-ranker behind an interface, **off by default**, no keys in the repo.

### Outputs
- `classification_results` (asset_id, top-3 candidates, scores, chosen code, confidence band, matched-term explanation).
- Confidence policy: auto-accept ≥ τ_high; review queue between τ_low and τ_high; reject below. Choose thresholds on the dev set to hit ≥ 95% precision for auto-accepts; report the resulting auto-accept rate.
- **Streamlit review UI:** accept / override / note; decisions saved to `human_decisions` and fed back into `synonyms.csv` (active-learning loop).
- Metrics: top-1 and top-3 accuracy per method, precision/recall of auto-accept, confusion on the most-confused pairs, calibration plot, error analysis (`docs/error_analysis.md`).

### Acceptance
- All reported numbers reproduced by `make eval` from fixed seeds; numbers pasted into the README exactly as measured.
- Normaliser unit-tested; no secrets; pipeline can run offline after model download.
- Review UI round-trip test (decision → synonyms update → improved or unchanged accuracy on dev).

---

## How this implementation deviates from the spec (read with the spec)

| Spec | This implementation | Why |
|---|---|---|
| Official NBS Uniclass 2015 tables as reference data | **Not obtained.** `data/mock_uniclass_dev_placeholder.csv` (96 rows, 49 Products / 47 Systems) is a non-authoritative placeholder; `is_mock()` propagates into every output row and `--final` raises `MockDataError`. | The NBS download is login-gated and JS-rendered (`scripts/fetch_uniclass.py` logs the attempt and falls back). Hard rule: never invent codes, so nothing is presented as an official code list. See `docs/OPEN_QUESTIONS.md` §2. |
| Golden set labels drafted against the *official* table, human reviews ≥ 20% before accuracy is reported | Labels were drafted against the **placeholder** code list; `review_sample.csv` (264 rows = 20.0% of 1,324) is generated for human review and **the human review is still outstanding** (0 of 264 reviewed). | The same blocker as above: labels cannot be verified against official titles. All reported accuracy is therefore a **self-consistency measure on synthetic labels**, not evidence of real-world Uniclass accuracy. |
| `make eval` | `make p13-eval` (root `Makefile`), `python projects/p13-uniclass-mapper/src/eval.py --seed 42`. | Root Makefile owns the target namespace (see the `p12-run` precedent). |
| scikit-learn / numpy-FAISS retrieval | numpy cosine over a cached `uniclass_embeddings.npz`; scikit-learn is not used. | The code list is 96 rows — FAISS is overkill, and dropping the dependency keeps the offline path smaller. Trivial to swap for FAISS later (same interface). |
| Optional LLM re-ranker behind an interface, off by default | **Not implemented**; documented as a seam in §7 of the README instead. | No key can be added to this repo and there was no way to verify an external API contract; an unused, untested abstraction would be dead code. |
| DuckDB in the stack | DuckDB is used only as an optional inspection tool in the README's validation SQL; the pipeline is CSV in / CSV out. | Outputs are small (96-code vocabulary); a database dependency would add nothing. |