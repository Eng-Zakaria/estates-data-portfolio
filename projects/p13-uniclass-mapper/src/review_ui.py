"""Streamlit review UI for P13 Uniclass mapper.

Run: streamlit run projects/p13-uniclass-mapper/src/review_ui.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Allow `streamlit run <path>/src/review_ui.py` from any working directory.
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline import UniclassMapper  # noqa: E402
from synonyms import record_decision as record_synonym  # noqa: E402

# P13_DATA_DIR lets tests (and a reviewer with a copy of the data) point the UI at
# a scratch directory instead of the committed one.
DATA_DIR = Path(os.environ.get("P13_DATA_DIR", SRC_DIR.parent / "data"))
GOLDEN_SET_PATH = DATA_DIR / "golden_set.csv"
REVIEW_SAMPLE_PATH = DATA_DIR / "review_sample.csv"
HUMAN_DECISIONS_PATH = DATA_DIR / "human_decisions.csv"
SYNONYMS_PATH = DATA_DIR / "synonyms.csv"

st.set_page_config(page_title="Uniclass Mapper Review (synthetic)", layout="wide")
st.title("Uniclass 2015 Mapper — Human Review (NON-AUTHORITATIVE placeholder codes)")
st.caption(
    "Synthetic data for portfolio demonstration. Reference code list is the "
    "non-authoritative placeholder (is_mock=true) until the official NBS Uniclass "
    "2015 tables are supplied — see docs/SOURCES.md."
)


@st.cache_data
def load_golden_set():
    try:
        return pd.read_csv(GOLDEN_SET_PATH)
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data
def load_review_sample():
    try:
        return pd.read_csv(REVIEW_SAMPLE_PATH)
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data
def load_human_decisions():
    try:
        return pd.read_csv(HUMAN_DECISIONS_PATH)
    except FileNotFoundError:
        return pd.DataFrame(columns=["description", "true_code", "human_code", "notes"])


@st.cache_data
def load_synonyms():
    try:
        df = pd.read_csv(SYNONYMS_PATH, dtype=str).fillna("")
        if "phrase" not in df.columns and "synonym" in df.columns:
            df = df.rename(columns={"synonym": "phrase"})
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["phrase", "code"])


def save_human_decisions(df: pd.DataFrame) -> None:
    HUMAN_DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(HUMAN_DECISIONS_PATH, index=False)


def save_synonyms(df: pd.DataFrame) -> None:
    SYNONYMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SYNONYMS_PATH, index=False)


@st.cache_resource
def get_mapper():
    return UniclassMapper()


def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Page",
        ["Review Queue", "Bulk Classify", "Synonyms", "Statistics"],
    )

    golden = load_golden_set()
    review = load_review_sample()
    decisions = load_human_decisions()
    synonyms = load_synonyms()
    mapper = get_mapper()

    if page == "Review Queue":
        review_queue_page(golden, review, decisions, synonyms, mapper)
    elif page == "Bulk Classify":
        bulk_classify_page(mapper)
    elif page == "Synonyms":
        synonyms_page(synonyms)
    elif page == "Statistics":
        statistics_page(golden, decisions)


def review_queue_page(golden, review, decisions, synonyms, mapper):
    st.header("Review Queue")

    if len(review) == 0:
        st.info("No review sample found. Run `build_golden_set()` first.")
        return

    st.write(f"Total items in review queue: {len(review)}")
    st.write(f"Decisions made: {len(decisions)}")

    # Show progress
    decided = len(decisions)
    progress = decided / len(review) if len(review) > 0 else 0
    st.progress(progress)
    st.write(f"Progress: {decided}/{len(review)} ({progress * 100:.1f}%)")

    # Show undecided items
    decided_descriptions = set(decisions["description"].tolist()) if len(decisions) > 0 else set()
    undecided = review[~review["description"].isin(decided_descriptions)]

    if len(undecided) == 0:
        st.success("All items reviewed!")
        return

    # Show first undecided item
    item = undecided.iloc[0]
    st.subheader(f"Item {review.index.get_loc(item.name) + 1} of {len(review)}")

    # Show description and auto prediction
    st.write("**Description:**")
    st.code(item["description"])

    st.caption(
        "Reference codes come from the non-authoritative placeholder list "
        "(is_mock=true), not the official NBS Uniclass 2015 tables."
    )
    prediction = mapper.classify(item["description"])

    st.write("**Auto Prediction:**")
    col1, col2, col3 = st.columns(3)
    col1.metric("Code", prediction.get("code", "N/A"))
    col2.metric("Confidence", prediction.get("confidence_band", "N/A"))
    col3.metric("Hybrid Score", f"{prediction.get('hybrid_score', 0):.3f}")

    if prediction.get("matched"):
        st.write(f"**Title:** {prediction.get('title', 'N/A')}")
        st.write(
            f"Fuzzy: {prediction.get('fuzzy_score', 0):.1f} | "
            f"Embedding: {prediction.get('embedding_score', 0):.3f} | "
            f"Keyword: {prediction.get('keyword_score', 0):.2f}"
        )
        st.write(f"Matched terms: {prediction.get('matched_terms', [])}")

    # True code (for reference)
    st.write(f"**True Code (hidden in real use):** {item['true_code']} ({item['table']})")

    # Decision form
    st.write("---")
    st.write("**Your Decision:**")

    col1, col2 = st.columns(2)
    with col1:
        decision = st.radio(
            "Decision",
            ["Accept", "Override", "Reject", "Skip"],
            horizontal=True,
        )

    override_code = ""
    if decision == "Override":
        override_code = st.text_input("Correct Code", placeholder="e.g., Pr_50_20_10")

    notes = st.text_area("Notes (optional)", placeholder="Any notes about this decision...")

    if st.button("Submit Decision", type="primary"):
        new_decision = {
            "description": item["description"],
            "true_code": item["true_code"],
            "human_code": override_code
            if decision == "Override"
            else (item["true_code"] if decision == "Accept" else ""),
            "decision": decision,
            "notes": notes,
            "auto_code": prediction.get("code", ""),
            "auto_confidence": prediction.get("confidence_band", ""),
        }

        # Append to decisions
        decisions = pd.concat([decisions, pd.DataFrame([new_decision])], ignore_index=True)
        save_human_decisions(decisions)

        # If override, feed the active-learning loop (synonyms.csv)
        if decision == "Override" and override_code:
            record_synonym(item["description"], override_code, SYNONYMS_PATH)
            load_synonyms.clear()

        st.success("Decision saved!")
        st.rerun()

    # Show previous decisions
    if len(decisions) > 0:
        st.write("---")
        st.write("**Previous Decisions:**")
        st.dataframe(decisions[["description", "decision", "human_code", "notes"]], use_container_width=True)


def bulk_classify_page(mapper):
    st.header("Bulk Classification")
    st.write("Upload a CSV file with a description column to classify multiple items.")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.write(f"Loaded {len(df)} rows")
        st.write("Columns:", df.columns.tolist())

        desc_col = st.selectbox("Description column", df.columns.tolist())
        table_filter = st.selectbox("Table filter (optional)", ["None", "Products", "Systems"])
        table = None if table_filter == "None" else table_filter

        if st.button("Classify All"):
            with st.spinner("Classifying..."):
                out = mapper.classify_dataframe(df, description_col=desc_col, table=table)
                st.success(f"Classified {len(out)} rows")
                st.dataframe(out.head(50), use_container_width=True)


def synonyms_page(synonyms):
    st.header("Synonyms Dictionary")
    st.write("Active learning loop: human overrides are added here to improve future predictions.")

    if len(synonyms) > 0:
        st.dataframe(synonyms, use_container_width=True)
    else:
        st.info("No synonyms yet. Override decisions in Review Queue will populate this.")

    st.write("---")
    st.write("**Add Synonym Manually:**")
    col1, col2 = st.columns(2)
    with col1:
        new_synonym = st.text_input("Synonym / Description")
    with col2:
        new_code = st.text_input("Uniclass Code")

    if st.button("Add Synonym") and new_synonym and new_code:
        record_synonym(new_synonym, new_code, SYNONYMS_PATH)
        load_synonyms.clear()
        st.success("Synonym added!")
        st.rerun()


def statistics_page(golden, decisions):
    st.header("Statistics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Golden Set Size", len(golden))
    col2.metric("Decisions Made", len(decisions))
    if len(golden) > 0:
        col3.metric("Review Progress", f"{len(decisions) / len(golden) * 100:.1f}%")

    if len(decisions) > 0:
        st.write("**Decision Distribution:**")
        dec_counts = decisions["decision"].value_counts()
        st.bar_chart(dec_counts)

        st.write("**Agreement with Auto:**")
        # Compare human vs auto
        decisions["agree"] = decisions.apply(
            lambda r: (
                "Yes"
                if r["decision"] == "Accept" and r["auto_code"] == r["true_code"]
                else ("Partial" if r["decision"] == "Override" else "No")
            ),
            axis=1,
        )
        agree_counts = decisions["agree"].value_counts()
        st.bar_chart(agree_counts)


if __name__ == "__main__":
    main()
