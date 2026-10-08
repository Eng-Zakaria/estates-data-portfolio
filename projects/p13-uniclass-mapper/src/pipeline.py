"""Pipeline orchestrator for P13 Uniclass mapper."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from hybrid import (
    CONFIDENCE_THRESHOLDS,
    batch_classify,
    batch_hybrid_match,
    classify_with_confidence,
    hybrid_match,
)
from reference import get_warning, is_mock


class MockDataError(RuntimeError):
    """Raised when a caller requests FINAL outputs from mock placeholder data."""


class UniclassMapper:
    """Main pipeline class for Uniclass classification."""

    def __init__(
        self,
        table: str | None = None,
        weights: dict | None = None,
        synonyms_path: str | None = None,
        thresholds: dict | None = None,
    ):
        self.table = table
        self.weights = weights
        self.synonyms_path = synonyms_path
        # None = ship defaults from hybrid.CONFIDENCE_THRESHOLDS; pass the
        # dev-tuned policy (data/metrics.json) to reproduce the eval bands.
        self.thresholds = thresholds

    def classify(
        self,
        description: str,
        table: str | None = None,
    ) -> dict:
        """Classify a single description."""
        return classify_with_confidence(description, table or self.table, self.synonyms_path, self.thresholds)

    def classify_top3(
        self,
        description: str,
        table: str | None = None,
    ) -> list[dict]:
        """Top-3 candidates for one description (for classification_results)."""
        return hybrid_match(description, table or self.table, limit=3, synonyms_path=self.synonyms_path)

    def classify_batch(
        self,
        descriptions: list[str],
        table: str | None = None,
    ) -> list[dict]:
        """Classify multiple descriptions."""
        return batch_classify(descriptions, table or self.table, self.synonyms_path, self.thresholds)

    def classify_dataframe(
        self,
        df: pd.DataFrame,
        description_col: str = "description",
        table: str | None = None,
    ) -> pd.DataFrame:
        """Classify descriptions in a DataFrame column.

        Output columns (the `classification_results` contract): asset_id (if
        present in input, else row number), top-3 candidates with scores, chosen
        code, confidence band, matched-term explanation, plus a mock-data flag.
        """
        descs = df[description_col].astype(str).tolist()
        results = self.classify_batch(descs, table or self.table)
        top3 = batch_hybrid_match(
            descs,
            table or self.table,
            limit=3,
            thresholds=self.thresholds,
            synonyms_path=self.synonyms_path,
        )
        rows = []
        for r, cands in zip(results, top3):
            rows.append(
                {
                    "chosen_code": r.get("code"),
                    "chosen_title": r.get("title"),
                    "hybrid_score": r.get("hybrid_score"),
                    "confidence_band": r.get("confidence_band"),
                    "matched_terms": ";".join(r.get("matched_terms", [])),
                    "cand_1": cands[0]["code"] if len(cands) > 0 else "",
                    "cand_1_score": cands[0]["hybrid_score"] if len(cands) > 0 else "",
                    "cand_2": cands[1]["code"] if len(cands) > 1 else "",
                    "cand_2_score": cands[1]["hybrid_score"] if len(cands) > 1 else "",
                    "cand_3": cands[2]["code"] if len(cands) > 2 else "",
                    "cand_3_score": cands[2]["hybrid_score"] if len(cands) > 2 else "",
                    "is_mock": bool(is_mock()),
                }
            )
        result_df = pd.DataFrame(rows)
        base = df.reset_index(drop=True)
        if "asset_id" not in base.columns:
            base = base.copy()
            base["asset_id"] = base.index
        return pd.concat([base, result_df], axis=1)

    def save_results(
        self,
        df: pd.DataFrame,
        output_path: str,
        description_col: str = "description",
    ) -> None:
        """Save classification results to CSV."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")


def run_pipeline(
    input_path: str,
    output_path: str,
    description_col: str = "description",
    table: str | None = None,
    final: bool = False,
    tau_high: float | None = None,
    tau_low: float | None = None,
) -> None:
    """Run the full classification pipeline on a CSV file.

    With mock placeholder reference data the pipeline always stamps outputs
    `is_mock=True` and prints the non-authoritative warning; passing
    `final=True` refuses to write (exit via MockDataError) per the spec.

    `tau_high` / `tau_low` override the shipped confidence bands with the
    dev-tuned policy reported in data/metrics.json.
    """
    if final and is_mock():
        raise MockDataError(
            "Refusing FINAL output from NON-AUTHORITATIVE mock Uniclass data. "
            "Official source: https://uniclass.thenbs.com/download. " + get_warning()
        )
    if is_mock():
        print(get_warning())
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    if "description" not in df.columns and description_col not in df.columns:
        raise ValueError(f"Description column '{description_col}' not found in input")

    # Use the specified description column
    desc_col = description_col if description_col in df.columns else "description"

    print(f"Classifying {len(df)} descriptions...")

    thresholds = dict(CONFIDENCE_THRESHOLDS)
    if tau_high is not None:
        thresholds["auto_accept"] = tau_high
    if tau_low is not None:
        thresholds["review_lower"] = min(tau_low, thresholds["auto_accept"])

    mapper = UniclassMapper(table=table, thresholds=thresholds)
    result_df = mapper.classify_dataframe(df, description_col=desc_col)

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)

    print(f"Results saved to {output_path}")
    print(f"Classified {len(result_df)} rows")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="P13 Uniclass classification pipeline")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", required=True, help="Output CSV file")
    parser.add_argument("--desc-col", default="description", help="Description column name")
    parser.add_argument("--table", choices=["Products", "Systems"], help="Filter by table")
    parser.add_argument("--tau-high", type=float, help="Auto-accept threshold (default 0.85; dev-tuned 0.30)")
    parser.add_argument("--tau-low", type=float, help="Review-queue lower threshold (default 0.45)")
    parser.add_argument(
        "--final",
        action="store_true",
        help="Require authoritative reference data (refuses mock output)",
    )
    args = parser.parse_args()

    run_pipeline(
        args.input,
        args.output,
        args.desc_col,
        args.table,
        args.final,
        args.tau_high,
        args.tau_low,
    )


if __name__ == "__main__":
    main()
