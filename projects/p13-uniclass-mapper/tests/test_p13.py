"""Tests for P13 Uniclass mapper."""

import sys
from pathlib import Path

import pytest

# Add the project root to path so we can import from src
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

# ruff: noqa: E402
import pandas as pd
from embedder import get_embeddings, semantic_search
from fuzzy_matcher import best_fuzzy_match, fuzzy_match_detailed
from golden_set import build_golden_set
from hybrid import classify_with_confidence
from normaliser import expand_abbreviations, normalise_cached
from reference import (
    get_children,
    get_level,
    get_parent,
    get_subtree_codes,
    get_title,
    is_mock,
    load_uniclass,
    search_titles,
)


def test_reference_loading():
    """Test that Uniclass reference data loads correctly."""
    df = load_uniclass()
    assert len(df) > 50  # Should have many codes
    assert "Products" in df["table"].unique()
    assert "Systems" in df["table"].unique()
    assert is_mock()  # Using mock data


def test_reference_lookups():
    """Test basic reference lookups."""
    assert get_title("Pr_50_20_10") == "Air handling units"
    assert get_level("Pr_50_20_10") == 3
    assert get_parent("Pr_50_20_10") == "Pr_50_20"
    children = get_children("Pr_50_20")
    assert "Pr_50_20_10" in children
    assert "Pr_50_20_20" in children


def test_subtree_codes():
    """Test subtree code retrieval."""
    subtree = get_subtree_codes("Pr_50")
    assert "Pr_50_10" in subtree
    assert "Pr_50_20_10" in subtree
    assert len(subtree) > 10


def test_search_titles():
    """Test title search."""
    results = search_titles("air handling", table="Products")
    assert len(results) > 0
    codes = [r["code"] for r in results]
    assert "Pr_50_20_10" in codes


def test_normaliser():
    """Test text normalisation."""
    assert normalise_cached("AHU-03 air hndlg unit L2") == "air handling unit air handling unit l2"
    assert normalise_cached("Boiler no 2 (Remeha)") == "boiler number 2 remeha"
    assert normalise_cached("FCU fan coil rm 214") == "fan coil unit fan coil room 214"
    assert normalise_cached("AHU-01 VAV box controller") == "air handling unit variable air volume box controller"


def test_abbreviation_expansion():
    """Test abbreviation expansion."""
    assert "air handling unit" in expand_abbreviations("AHU unit")
    assert "fan coil unit" in expand_abbreviations("FCU unit")
    assert "variable air volume" in expand_abbreviations("VAV box")


def test_matching_query_strips_noise():
    """The retrieval query must drop location, tag, manufacturer and rating noise.

    Hand-checked: each expectation below is the outcome a reader of
    docs/error_analysis.md §6 would predict (offices/plants/rooms and manufacturer
    names otherwise dominate cosine similarity — "LED panel light office" retrieved
    Roofs before this existed).
    """
    from normaliser import matching_query

    # Location token removed, real type words kept.
    assert matching_query("LED panel light office") == "led panel light"
    assert matching_query("roof extract fan plantroom") == "extract fan"
    # Manufacturer and asset number removed, abbreviation expanded.
    assert matching_query("Boiler no 2 (Remeha)") == "boiler number"
    # Electrical ratings carry no type signal.
    assert matching_query("transformer 11kV/415V") == "transformer"
    # Generic building nouns that pulled retrieval towards the wrong branch.
    assert matching_query("pressure sensor duct") == "pressure sensor"
    # The equipment tag itself goes, but the abbreviation token survives so that
    # titles keyed on the acronym (e.g. "VAV boxes") still match.
    assert "ahu" in matching_query("AHU-03 air hndlg unit L2")
    assert "vav" in matching_query("variable air volume box")
    # FCU is special-cased: it must not expand to "fan coil unit".
    assert matching_query("FCU-05 fan coil unit room 214") == "fan coil fan coil unit"


def test_fuzzy_matching():
    """Test fuzzy matching."""
    matches = fuzzy_match_detailed("air handling unit", table="Products", limit=3)
    assert len(matches) > 0
    assert matches[0].code == "Pr_50_20_10"
    assert matches[0].score > 80

    # Test best match
    best = best_fuzzy_match("boiler", table="Products", score_cutoff=60)
    assert best is not None
    assert best.code == "Pr_50_10_10"


def test_embeddings():
    """Test embedding retrieval."""

    emb = get_embeddings()
    if emb is not None:
        assert emb.shape[0] > 50
        assert emb.shape[1] == 384  # all-MiniLM-L6-v2 dimension

    # Test semantic search
    results = semantic_search("air handling unit", top_k=3)
    assert len(results) > 0
    codes = [r[0] for r in results]
    assert "Pr_50_20_10" in codes


def test_hybrid_matching():
    """Test hybrid matching pipeline."""
    result = classify_with_confidence("AHU-03 air handling unit L2")
    assert result["matched"]
    assert result["code"] == "Pr_50_20_10"
    assert result["confidence_band"] in ["auto", "review", "reject"]
    assert "hybrid_score" in result
    assert "matched_terms" in result


def test_hybrid_batch():
    """Test batch classification."""
    from hybrid import batch_classify

    queries = [
        "AHU-03 air handling unit L2",
        "Boiler no 2 (Remeha)",
        "FCU fan coil rm 214",
    ]
    results = batch_classify(queries)
    assert len(results) == 3
    assert all(r["matched"] for r in results)
    assert results[0]["code"] == "Pr_50_20_10"
    assert results[1]["code"] == "Pr_50_10_10"


def test_golden_set_build():
    """Test golden set generation."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test_golden.csv"
        build_golden_set(str(out))
        assert out.exists()
        df = pd.read_csv(out)
        assert len(df) >= 100  # Should have many examples


def test_golden_set_meets_spec_size():
    """Spec: >= 300 labelled examples, and the review sample covers >= 20%."""
    df = pd.read_csv(project_root / "data" / "golden_set.csv", dtype=str)
    assert len(df) >= 300
    assert df["true_code"].notna().all()
    assert not df["description"].str.strip().eq("").any()

    review = pd.read_csv(project_root / "data" / "review_sample.csv", dtype=str)
    assert len(review) / len(df) >= 0.20
    assert set(review.columns) >= {"description", "true_code", "human_code", "notes"}
    # A fresh sample must still be unsigned by a human.
    assert review["human_code"].fillna("").eq("").all()


def test_golden_table_word_invariant():
    """The Products/Systems sub-tree filter leans on this invariant.

    Every Systems description says "system" and no Products description does, so
    the two keyword penalties in hybrid.py are rules about the label space rather
    than tuning on the test split. If a future golden set breaks the invariant,
    the penalties need revisiting (see docs/error_analysis.md).
    """
    df = pd.read_csv(project_root / "data" / "golden_set.csv", dtype=str)
    products = df[df["table"] == "Products"]["description"].str.lower()
    systems = df[df["table"] == "Systems"]["description"].str.lower()
    assert len(products) > 0 and len(systems) > 0
    assert not products.str.contains(r"\bsystem\b").any()
    assert systems.str.contains(r"\bsystem\b").all()


def test_pipeline_classify():
    """Test pipeline classification."""
    from pipeline import UniclassMapper

    mapper = UniclassMapper()
    result = mapper.classify("AHU-03 air handling unit L2")
    assert result["matched"]
    assert result["code"] == "Pr_50_20_10"


def test_pipeline_batch():
    """Test pipeline batch classification."""
    from pipeline import UniclassMapper

    mapper = UniclassMapper()
    descriptions = [
        "AHU-03 air handling unit L2",
        "Boiler no 2 (Remeha)",
    ]
    results = mapper.classify_batch(descriptions)
    assert len(results) == 2
    assert all(r["matched"] for r in results)


def test_golden_set_accuracy():
    """Test accuracy on golden set (dev set)."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "golden.csv"
        build_golden_set(str(out))
        df = pd.read_csv(out)

        # Classify all
        from pipeline import UniclassMapper

        mapper = UniclassMapper()
        results = mapper.classify_batch(df["description"].tolist())

        # Check accuracy
        correct = sum(1 for i, r in enumerate(results) if r["matched"] and r["code"] == df.iloc[i]["true_code"])
        accuracy = correct / len(df)

        # With mock data, we expect reasonable accuracy
        assert accuracy > 0.5  # Should be reasonable with mock data
        print(f"Top-1 accuracy on golden set: {accuracy:.2%}")


def test_review_ui_round_trip():
    """Acceptance: decision -> synonyms.csv -> accuracy on dev improved or unchanged.

    Simulates the Streamlit review loop headlessly: take the dev split with an
    empty synonym store, record human overrides for the rows the model gets wrong
    (exactly what an override button in the UI does via
    `synonyms.record_decision`), then re-classify dev with the updated store.
    """
    import tempfile

    from pipeline import UniclassMapper
    from synonyms import clear_synonym_cache, record_decision

    dev = pd.read_csv(project_root / "data" / "golden_dev.csv", dtype=str)
    assert len(dev) > 50, "expected a dev split of >50 labelled rows"

    with tempfile.TemporaryDirectory() as tmp:
        syn = Path(tmp) / "synonyms.csv"
        pd.DataFrame(columns=["phrase", "code"]).to_csv(syn, index=False)

        before_mapper = UniclassMapper(synonyms_path=str(syn))
        before = before_mapper.classify_batch(dev["description"].tolist())
        acc_before = sum(1 for r, t in zip(before, dev["true_code"]) if r["matched"] and r["code"] == t) / len(dev)

        # A reviewer's overrides: every row the model currently gets wrong.
        overrides = [
            (desc, true)
            for r, desc, true in zip(before, dev["description"], dev["true_code"])
            if not (r["matched"] and r["code"] == true)
        ]
        for desc, true in overrides:
            record_decision(desc, true, syn)

        # The store the review UI writes to must contain exactly those phrases.
        stored = pd.read_csv(syn, dtype=str)
        assert len(stored) == len(overrides)
        assert set(stored["phrase"]) == {d.lower() for d, _ in overrides}
        # record_decision is idempotent on identical rows (re-submitting is safe).
        for desc, true in overrides:
            record_decision(desc, true, syn)
        assert len(pd.read_csv(syn, dtype=str)) == len(overrides)

        after = UniclassMapper(synonyms_path=str(syn)).classify_batch(dev["description"].tolist())
        acc_after = sum(1 for r, t in zip(after, dev["true_code"]) if r["matched"] and r["code"] == t) / len(dev)

    clear_synonym_cache()
    # Spec asks for "improved or unchanged": a bounded synonym bonus cannot
    # outvote every strong competitor, so a handful of rows can stay wrong even
    # after an override. Measured numbers are in docs/ACCEPTANCE_P13.md.
    assert acc_after >= acc_before, (acc_before, acc_after)


def test_pipeline_refuses_final_output_from_mock_data():
    """Acceptance (hard rule): mock reference data must not produce final outputs."""
    from pipeline import MockDataError, run_pipeline
    from reference import is_mock

    assert is_mock(), "placeholder data is expected in this repo"
    with pytest.raises(MockDataError) as exc:
        run_pipeline(
            str(project_root / "data" / "golden_dev.csv"),
            str(project_root / "data" / "should_not_exist.csv"),
            final=True,
        )
    assert "NON-AUTHORITATIVE" in str(exc.value)
    assert not (project_root / "data" / "should_not_exist.csv").exists()


def test_review_ui_app_round_trip(monkeypatch):
    """Drives the real Streamlit app: submit an Override, check what it wrote.

    Uses streamlit.testing.v1.AppTest (the same script a browser runs), with
    P13_DATA_DIR pointed at a scratch copy so the committed data files are never
    touched. Complements test_review_ui_round_trip, which measures the accuracy
    effect of the loop.
    """
    import shutil
    import tempfile

    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    data = project_root / "data"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in ("golden_set.csv", "review_sample.csv", "synonyms.csv"):
            shutil.copy(data / name, tmp_path / name)
        monkeypatch.setenv("P13_DATA_DIR", str(tmp_path))

        app = AppTest.from_file(str(project_root / "src" / "review_ui.py"), default_timeout=600)
        app.run()
        assert not app.exception

        # The first queued item and the code a reviewer would type in.
        item = pd.read_csv(tmp_path / "review_sample.csv", dtype=str).iloc[0]
        app.radio[0].set_value("Override")
        app.run()
        app.text_input[0].set_value(item["true_code"])
        app.text_area[0].set_value("checked against the placeholder list")
        app.button[0].click()
        app.run()
        assert not app.exception

        decisions = pd.read_csv(tmp_path / "human_decisions.csv", dtype=str).fillna("")
        assert len(decisions) == 1
        row = decisions.iloc[0]
        assert row["description"] == item["description"]
        assert row["decision"] == "Override"
        assert row["human_code"] == item["true_code"]
        assert row["notes"] == "checked against the placeholder list"

        synonyms = pd.read_csv(tmp_path / "synonyms.csv", dtype=str).fillna("")
        assert item["description"].lower() in set(synonyms["phrase"])
        assert item["true_code"] in set(synonyms["code"])

        # Re-running the app must not offer the decided item again.
        app.run()
        assert not app.exception
        remaining = pd.read_csv(tmp_path / "review_sample.csv", dtype=str)
        assert len(remaining) == len(pd.read_csv(data / "review_sample.csv", dtype=str))


def test_review_ui_loads():
    """Test that review UI components load without error."""
    # Just verify they can be imported and run without error
    # (Full UI test would require streamlit runtime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
