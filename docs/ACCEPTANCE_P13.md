# ACCEPTANCE — P13 Uniclass classification mapper

Measured 2026-10-08, seed 42, on synthetic data. Reference code list is the
**non-authoritative placeholder** (`data/mock_uniclass_dev_placeholder.csv`); no official
Uniclass 2015 code is asserted anywhere. No real building data, no real asset register,
no real compliance or classification claim.

Spec acceptance criteria (from `docs/specs/03-bim-standards-p11-p14.md` §P13):

## A1. "All reported numbers reproduced by `make eval` from fixed seeds"

`make` is not installed in this environment (same as P12/P14), so the target's command
was run directly — `make p13-eval` is `python projects/p13-uniclass-mapper/src/eval.py`.

```
$ python projects/p13-uniclass-mapper/src/eval.py            # ~4 min, seed 42
...
  "splits": {"train": 909, "dev": 187, "test": 228}
  "thresholds": {"tau_high": 0.3, "tau_low": 0.3, "tuned_on": "dev",
                 "precision": 0.984, "rate": 1.0}
```

Re-run reproducibility (SHA-256 compared across two consecutive runs):

```
metrics.json identical:    True
golden_test.csv identical: True
confusion_test.csv identical: True
```

Measured headline numbers (full table in the project README §5, analysis in
`projects/p13-uniclass-mapper/docs/error_analysis.md`):

| | fuzzy | embedding | hybrid |
|---|---|---|---|
| test top-1 (n=228) | 21.49% | 57.02% | **97.81%** |
| test top-3 (n=228) | 60.96% | 81.14% | **99.56%** |

Auto-accept: dev 187/187 at **98.40%** precision (target ≥ 95% ✔); test 227/228 at
98.24%. τ_high = 0.30 tuned on dev only; the empty review band is explained in
`error_analysis.md` §2 and flagged in the README, not glossed over.

## A2. "Normaliser unit-tested; no secrets; pipeline can run offline after model download"

```
$ python -m pytest projects/p13-uniclass-mapper/tests/ -q --no-cov -p no:cacheprovider
21 passed in 160.37s (0:02:40)
$ python -m ruff check projects/p13-uniclass-mapper/
All checks passed!
$ python -m ruff format --check projects/p13-uniclass-mapper/
16 files already formatted
```

- Normaliser fixtures are hand-checked (`test_normaliser`,
  `test_abbreviation_expansion`, `test_matching_query_strips_noise`).
- Secrets: no API keys, no `.env` additions, no network calls in the classification
  path. `src/review_ui.py` and `src/eval.py` import no LLM client; the optional LLM
  re-ranker from the spec is documented as a seam (README §6/§8), not implemented.
- Offline: `sentence-transformers/all-MiniLM-L6-v2` is cached in
  `data/reference/embeddings/` (gitignored — model weights are never committed, AGENTS.md
  rule 10) and the title vectors are content-addressed by a SHA-1 of `code\ttitle` +
  `version`, so the cache cannot go stale when the reference table is replaced. Measured:
  a second `eval.py` run reuses the cache and returns identical metrics.

CLI, tuned policy (reproduces the dev/test band counts above):

```
$ python projects/p13-uniclass-mapper/src/pipeline.py \
    --input projects/p13-uniclass-mapper/data/golden_dev.csv \
    --output projects/p13-uniclass-mapper/data/classification_results_demo.csv \
    --tau-high 0.30
Classifying 187 descriptions...
Results saved to projects\p13-uniclass-mapper\data\classification_results_demo.csv
Classified 187 rows

confidence_band counts: {'auto': 187}      # matches dev auto-accept = 187/187
```

Sample rows (`data/classification_results_demo.csv`, `matched_terms` shown truncated):

| description | chosen_code | title | score | band | matched_terms |
|---|---|---|---|---|---|
| `AHU-03 air hndlg unit L2` | `Pr_50_20_10` | Air handling units | 0.999 | auto | word:air;word:handling;word:unit;tag:prefix |
| `Boiler no 2 (Remeha)` | `Pr_50_10_10` | Boilers | 0.707 | auto | word:boiler |
| `FCU-05 fan coil unit room 214` | `Pr_50_20_20` | Fan coil units | 1.000 | auto | word:coil;word:fan;word:unit;tag:prefix |
| `boiler feed pump` | `Pr_50_40_10` | Pumps | 0.890 | auto | syn:boiler feed pump;word:pump |

## A3. "Review UI round-trip test (decision → synonyms update → improved or unchanged accuracy on dev)"

`tests/test_p13.py::test_review_ui_round_trip` — passes. It runs the dev split against an
**empty** synonym store, records an override for every wrong row through
`synonyms.record_decision` (the same function `review_ui.py` calls on Override), asserts
the store contents and idempotency of re-submissions, then re-classifies:

| stage | dev top-1 (n=187) |
|---|---|
| empty `synonyms.csv` | 78.61% (147/187) |
| after 40 human overrides | **98.93%** (185/187) |

Two rows remain wrong after the override (`roof extract fan`,
`humidity sensor AHU`); both are analysed in `error_analysis.md` §5. The test asserts
*improved or unchanged* (spec wording), not a fabricated 100%.

The UI itself is also driven end to end, not just its logic:
`tests/test_p13.py::test_review_ui_app_round_trip` runs `src/review_ui.py` through
`streamlit.testing.v1.AppTest` (the same script a browser runs) with `P13_DATA_DIR`
pointed at a scratch copy, clicks **Override**, submits the correct code and a note,
and asserts `human_decisions.csv` gained exactly that row (description, decision,
`human_code`, notes, auto code/band), that `synonyms.csv` gained the phrase → code pair,
and that the decided item drops out of the queue on the next run. Measured: passes in
31.55 s. The committed `data/` files are untouched (verified: `synonyms.csv` still 52
rows, no `human_decisions.csv`).

## A4. Hard rule: "pipeline can never present mock data as final"

`tests/test_p13.py::test_pipeline_refuses_final_output_from_mock_data` — passes:

```
$ python projects/p13-uniclass-mapper/src/pipeline.py --input ... --final
MockDataError: Refusing FINAL output from NON-AUTHORITATIVE mock Uniclass data.
Official source: https://uniclass.thenbs.com/download. ...
(no output file written — asserted)
```

Also verified: `data/metrics.json` carries `"is_mock": true`, every row of
`classification_results_demo.csv` carries `is_mock`, and
`data/mock_uniclass_dev_placeholder.csv` has `is_mock=TRUE` on all 96 rows.

## A5. Spec compliance gaps recorded honestly

| Spec item | Status | Where |
|---|---|---|
| Official NBS Uniclass 2015 tables | **Not obtained** (login-gated; attempt logged) | `docs/SOURCES.md` §1, `docs/OPEN_QUESTIONS.md` §2, `DATA.md` |
| Golden set labelled against the *official* table | Labelled against the placeholder instead | `SPEC.md` deviations table |
| Human reviews ≥ 20% sample before accuracy is reported | Sample generated (265 = 20.02%); **0 reviewed** — human action outstanding | `data/review_sample.csv`, `tests/test_p13.py::test_golden_set_meets_spec_size` (asserts the sample is still unsigned) |
| Optional LLM re-ranker behind an interface, off by default | Not implemented (documented seam) | README §6, §8 |
| `make eval` | `make p13-eval` (root Makefile) | `Makefile` |
| scikit-learn / FAISS retrieval | numpy cosine (96-code vocabulary) | `SPEC.md` deviations table |

## Files

`README.md` (9-section template + Mermaid), `SPEC.md` (spec copy + deviations),
`docs/SOURCES.md` (provenance), `docs/error_analysis.md` (confusions, calibration,
threshold trade-off, review-loop measurement), `docs/img/calibration.svg` (generated),
`data/metrics.json` / `confusion_test.csv` / `calibration_test.csv` (regenerated by
`make p13-eval`), `data/classification_results_demo.csv` (187-row sample output).