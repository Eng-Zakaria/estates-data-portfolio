"""Evaluation for the P13 Uniclass mapper.

Compares all methods (fuzzy baseline, embedding retrieval, hybrid), tunes the
confidence thresholds on the dev split only, and reports final numbers on the
held-out test split. Everything is seeded; `make p13-eval` reproduces the
README numbers exactly.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from golden_set import build_golden_set, split_golden_set
from hybrid import (
    CONFIDENCE_THRESHOLDS,
    embedding_topk,
    fuzzy_topk,
    hybrid_match,
)
from pipeline import UniclassMapper

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"

METHODS = ("fuzzy", "embedding", "hybrid")


def _topk_codes(method: str, query: str, k: int = 3) -> list[str]:
    if method == "fuzzy":
        return [r["code"] for r in fuzzy_topk(query, limit=k)]
    if method == "embedding":
        return [r["code"] for r in embedding_topk(query, limit=k)]
    return [r["code"] for r in hybrid_match(query, limit=k)]


def method_accuracy(df: pd.DataFrame, method: str) -> dict:
    """Top-1 and top-3 accuracy for one method on a split (batched)."""
    descs = df["description"].astype(str).tolist()
    trues = df["true_code"].tolist()
    if method == "hybrid":
        from hybrid import batch_hybrid_match

        ranked = batch_hybrid_match(descs, limit=3)
        lists = [[r["code"] for r in qs] for qs in ranked]
    elif method == "embedding":
        from embedder import batch_semantic_search
        from normaliser import matching_query

        norms = [matching_query(d) or d for d in descs]
        lists = [[c for c, _s, _i in hits[:3]] for hits in batch_semantic_search(norms, top_k=3)]
    else:
        lists = [[r["code"] for r in fuzzy_topk(d, limit=3)] for d in descs]
    top1 = sum(1 for codes, t in zip(lists, trues) if codes and codes[0] == t)
    top3 = sum(1 for codes, t in zip(lists, trues) if t in codes)
    n = max(len(df), 1)
    return {
        "n": len(df),
        "top1": round(top1 / n, 4),
        "top3": round(top3 / n, 4),
        "top1_correct": top1,
        "top3_correct": top3,
    }


def tune_thresholds(
    df: pd.DataFrame,
    target_precision: float = 0.95,
) -> dict:
    """Sweep auto-accept thresholds on dev; pick the one with the best auto-accept
    rate among those hitting >= target precision (ties broken toward higher
    precision, then higher threshold). Never sees test."""
    from hybrid import batch_hybrid_match

    descs = df["description"].astype(str).tolist()
    trues = df["true_code"].tolist()
    ranked = batch_hybrid_match(descs, limit=1)
    scored = []
    for qs, true_code in zip(ranked, trues):
        if not qs:
            continue
        scored.append((qs[0]["hybrid_score"], qs[0]["code"] == true_code))
    best: dict | None = None
    for tau in [round(x / 100, 2) for x in range(30, 100, 5)]:
        auto = [c for s, c in scored if s >= tau]
        if not auto:
            continue
        prec = sum(auto) / len(auto)
        rate = len(auto) / len(scored)
        if prec >= target_precision:
            cand = {"tau_high": tau, "precision": round(prec, 4), "rate": round(rate, 4)}
            if best is None or (cand["rate"], cand["precision"]) > (best["rate"], best["precision"]):
                best = cand
    if best is None:
        # No threshold reaches target: report the most precise one honestly.
        tau = max((s for s, _ in scored), default=0.0)
        auto = [c for s, c in scored if s >= tau]
        prec = sum(auto) / max(len(auto), 1)
        best = {
            "tau_high": round(tau, 2),
            "precision": round(prec, 4),
            "rate": round(len(auto) / max(len(scored), 1), 4),
            "target_missed": True,
        }
    return best


def auto_accept_stats(df: pd.DataFrame, tau_high: float, tau_low: float) -> dict:
    """Precision/recall of the auto-accept band on a split (batched)."""
    from hybrid import batch_hybrid_match

    descs = df["description"].astype(str).tolist()
    trues = df["true_code"].tolist()
    ranked = batch_hybrid_match(descs, limit=1)
    auto_total = 0
    auto_correct = 0
    review = 0
    reject = 0
    for qs, true_code in zip(ranked, trues):
        if not qs:
            reject += 1
            continue
        pred = qs[0]["code"]
        score = qs[0]["hybrid_score"]
        if score >= tau_high:
            auto_total += 1
            if pred == true_code:
                auto_correct += 1
        elif score >= tau_low:
            review += 1
        else:
            reject += 1
    n = max(len(df), 1)
    return {
        "n": len(df),
        "tau_high": tau_high,
        "tau_low": tau_low,
        "auto_accept": auto_total,
        "auto_accept_rate": round(auto_total / n, 4),
        "auto_accept_precision": round(auto_correct / auto_total, 4) if auto_total else 0.0,
        "review": review,
        "reject": reject,
    }


def confusion_pairs(df: pd.DataFrame, limit: int = 10) -> list[dict]:
    """Most-confused (true -> predicted) pairs on a split (single pass)."""
    mapper = UniclassMapper()
    results = mapper.classify_batch(df["description"].astype(str).tolist())
    conf: Counter = Counter()
    for true, r in zip(df["true_code"], results):
        pred = r["code"] if r["matched"] else "NONE"
        if true != pred:
            conf[(true, pred)] += 1
    out = []
    for (true, pred), count in conf.most_common(limit):
        out.append({"true_code": true, "pred_code": pred, "count": count})
    return out


def calibration_table(df: pd.DataFrame, bins: int = 5) -> list[dict]:
    """Bin hybrid scores; report empirical top-1 accuracy per bin."""
    mapper = UniclassMapper()
    results = mapper.classify_batch(df["description"].astype(str).tolist())
    edges = [i / bins for i in range(bins + 1)]
    rows = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        in_bin = [
            (r["code"] == t) if r["matched"] else False
            for r, t in zip(results, df["true_code"])
            if (
                r.get("hybrid_score", 0) >= lo
                and (r.get("hybrid_score", 0) < hi or (i == bins - 1 and r.get("hybrid_score", 0) <= hi))
            )
        ]
        rows.append(
            {
                "bin_lo": round(lo, 2),
                "bin_hi": round(hi, 2),
                "n": len(in_bin),
                "empirical_accuracy": round(sum(in_bin) / len(in_bin), 4) if in_bin else 0.0,
                "mid": round((lo + hi) / 2, 2),
            }
        )
    return rows


def calibration_svg(calib: list[dict], out_path: Path) -> None:
    """Small dependency-free reliability diagram (perfect-calibration diagonal + observed)."""
    W, H, P = 420, 320, 44

    def x(v: float) -> float:
        return P + v * (W - 2 * P)

    def y(v: float) -> float:
        return H - P - v * (H - 2 * P)

    pts = " ".join(f"{x(r['mid']):.1f},{y(r['empirical_accuracy']):.1f}" for r in calib)
    circles = "\n".join(
        f'<circle cx="{x(r["mid"]):.1f}" cy="{y(r["empirical_accuracy"]):.1f}" r="5" '
        f'fill="#1f77b4"><title>n={r["n"]} acc={r["empirical_accuracy"]}</title></circle>'
        for r in calib
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" role="img" aria-label="Calibration plot">
<rect width="{W}" height="{H}" fill="white"/>
<line x1="{x(0)}" y1="{y(0)}" x2="{x(1)}" y2="{y(1)}" stroke="#999" stroke-dasharray="5,4"/>
<polyline points="{pts}" fill="none" stroke="#1f77b4" stroke-width="2"/>
{circles}
<text x="{W / 2}" y="{H - 8}" text-anchor="middle" font-size="12">mean predicted score (bin mid)</text>
<text x="12" y="{H / 2}" text-anchor="middle" font-size="12" transform="rotate(-90 12 {H / 2})">empirical acc</text>
</svg>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")


def evaluate(seed: int = 42, write_artifacts: bool = True) -> dict:
    """Full evaluation: build golden set, split, tune on dev, report on test."""
    golden_path = DATA_DIR / "golden_set.csv"
    build_golden_set(str(golden_path), seed=seed)
    df = pd.read_csv(golden_path, dtype=str)
    splits = split_golden_set(df, seed=seed)

    per_method = {split: {m: method_accuracy(splits[split], m) for m in METHODS} for split in ("train", "dev", "test")}
    tuned = tune_thresholds(splits["dev"])
    tau_high = tuned["tau_high"]
    # Review band must sit below the auto-accept threshold; clamp so the
    # (tau_low <= score < tau_high) band is well-formed even when the dev-tuned
    # auto-accept threshold falls below the default review floor.
    tau_low = min(CONFIDENCE_THRESHOLDS["review_lower"], tau_high)
    auto_stats = {split: auto_accept_stats(splits[split], tau_high, tau_low) for split in ("dev", "test")}
    conf = confusion_pairs(splits["test"])
    calib = calibration_table(splits["test"])

    metrics = {
        "seed": seed,
        "golden_n": len(df),
        "splits": {k: len(v) for k, v in splits.items()},
        "per_method": per_method,
        "thresholds": {"tau_high": tau_high, "tau_low": tau_low, "tuned_on": "dev", **tuned},
        "auto_accept": auto_stats,
        "confused_pairs_test": conf,
        "calibration_test": calib,
        "is_mock": True,
        "warning": "NON-AUTHORITATIVE mock Uniclass placeholder — development only, not final.",
    }
    if write_artifacts:
        (DATA_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        pd.DataFrame(conf).to_csv(DATA_DIR / "confusion_test.csv", index=False)
        pd.DataFrame(calib).to_csv(DATA_DIR / "calibration_test.csv", index=False)
        calibration_svg(calib, DOCS_DIR / "img" / "calibration.svg")
        for split, sdf in splits.items():
            sdf.to_csv(DATA_DIR / f"golden_{split}.csv", index=False)
    print(
        json.dumps({k: v for k, v in metrics.items() if k not in ("confused_pairs_test", "calibration_test")}, indent=2)
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="P13 evaluation (seeded, reproducible)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    evaluate(seed=args.seed, write_artifacts=not args.no_write)


if __name__ == "__main__":
    main()
