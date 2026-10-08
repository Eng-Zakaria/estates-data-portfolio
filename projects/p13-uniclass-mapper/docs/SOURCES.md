# P13 SOURCES — provenance for every code list and model used

Standing rule for this project (AGENTS.md hard rule 4): **standard codes are never
invented.** This file records what was actually obtained, what was *not* obtained, and
what must therefore not be trusted.

## 1. Uniclass 2015 (NBS) — NOT OBTAINED

| Field | Value |
|---|---|
| Official source | https://uniclass.thenbs.com/download (NBS / Uniclass) |
| Attempted | 2026-10-06 (`scripts/fetch_uniclass.py`), re-attempted 2026-10-08 |
| Outcome | **Failed.** The download page is JS-rendered and the table download is login-gated; an unauthenticated `urllib` request cannot obtain the CSV/Excel tables. Log: `data/uniclass_fetch.log` |
| What ships instead | `data/mock_uniclass_dev_placeholder.csv` — 96 rows (49 Products `Pr_`, 47 Systems `Ss_`) with columns `code, title, level, parent_code, table, version, source_url, retrieved_date, is_mock`; every row carries `is_mock=TRUE` |
| Status of those codes | **Non-authoritative.** They are a plausible-looking placeholder written for this project so the pipeline can be developed and tested. They have **not** been checked against the NBS tables and must never be presented as Uniclass 2015 codes |
| Licence of the placeholder | Ours (synthetic). The NBS Uniclass tables are **not** redistributed here — NBS terms of use have not been reviewed, so the real tables must be fetched by a human with an account |

Guard rails that keep the placeholder from leaking into a decision:

- `reference.is_mock()` is read from the table itself, so a real table flips it off
  automatically.
- Every output row carries an `is_mock` column (`pipeline.classify_dataframe`).
- `run_pipeline(..., final=True)` raises `MockDataError` and writes nothing
  (`tests/test_p13.py::test_pipeline_refuses_final_output_from_mock_data`).
- `data/metrics.json` carries `"is_mock": true` plus a warning string.

**To resolve:** a human downloads the Uniclass 2015 Products (`Pr`) and Systems (`Ss`)
tables from the NBS site, saves them as `data/uniclass_2015.csv` (same columns, or a
loader tweak recorded here), and the golden-set labels must then be re-checked against
the official titles before any accuracy number is quoted. Until then the accuracy in
the README is a **self-consistency measure on synthetic labels**.

## 2. Embedding model

| Field | Value |
|---|---|
| Model | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, ~90 MB cache) |
| Licence | Apache-2.0 |
| Used for | Title embeddings for the embedding-retrieval method (`src/embedder.py`) |
| Cached at | `data/reference/embeddings/` — **not committed** (`.gitignore`); model weights and derived vectors are rebuilt on first run, after which the pipeline runs offline |

## 3. Libraries

`rapidfuzz` (token-set ratio baseline), `sentence-transformers` + `numpy` (embedding
retrieval), `pandas` (tables), `streamlit` (review UI). No scikit-learn / FAISS: the
vocabulary is 96 codes, so a brute-force numpy cosine is both sufficient and one less
dependency to pin (see `SPEC.md`, deviations table).

## 4. Labels that are synthetic, not standard-derived

- Golden-set descriptions (1,324 rows) are written for this project: realistic messy
  asset descriptions crossed with locations, tags and manufacturers. They imitate the
  *style* of a CAFM asset register; no real register was copied.
- The true-code labels were drafted **against the placeholder code list** (§1), not
  against NBS titles.
- The abbreviation dictionary in `src/normaliser.py` (AHU, FCU, VAV, PRV, MCC, UPS …)
  is general estates vocabulary, not a standard. It is a development aid and should be
  reviewed by an estates practitioner before operational use.