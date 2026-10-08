"""Embedding-based retrieval using sentence-transformers (P13)."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import numpy as np

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from reference import get_uniclass_df

# Model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Small, fast, Apache 2.0 licence
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "reference" / "embeddings"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer | None:
    """Load the sentence transformer model (cached)."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return SentenceTransformer(EMBEDDING_MODEL, cache_folder=str(CACHE_DIR))


@lru_cache(maxsize=1)
def get_embeddings() -> np.ndarray | None:
    """Compute and cache embeddings for all Uniclass titles."""
    model = get_model()
    if model is None:
        return None

    df = get_uniclass_df()
    titles = df["title"].tolist()

    # Check cache. The key includes a hash of the (code, title) pairs and the
    # table version, so swapping the placeholder for the official tables (or
    # editing a title) can never silently reuse stale vectors.
    digest = hashlib.sha1(
        "\n".join(f"{c}\t{t}" for c, t in zip(df["code"], titles)).encode("utf-8")
        + str(sorted(set(df["version"]))).encode("utf-8")
    ).hexdigest()[:10]
    cache_file = CACHE_DIR / f"uniclass_embeddings_{len(df)}_{digest}.npy"
    if cache_file.exists():
        try:
            return np.load(cache_file)
        except Exception:
            pass

    # Compute embeddings
    embeddings = model.encode(titles, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

    # Save cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(cache_file, embeddings)

    return embeddings


def embed_query(query: str) -> np.ndarray | None:
    """Embed a single query string."""
    model = get_model()
    if model is None:
        return None
    return model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]


def embed_queries(queries: list[str]) -> np.ndarray | None:
    """Embed many queries in one model call (same normalisation as embed_query)."""
    model = get_model()
    if model is None:
        return None
    return np.asarray(model.encode(list(queries), convert_to_numpy=True, normalize_embeddings=True))


def semantic_search(
    query: str,
    table: str | None = None,
    top_k: int = 10,
    score_cutoff: float = 0.0,
) -> list[tuple[str, float, int]]:
    """Semantic search using cosine similarity on embeddings.

    Returns list of (code, score, index) tuples.
    """
    embeddings = get_embeddings()
    if embeddings is None:
        return []

    df = get_uniclass_df()
    mask = None
    if table:
        mask = (df["table"] == table).to_numpy()
        if not mask.any():
            return []

    query_emb = embed_query(query)
    if query_emb is None:
        return []

    # Compute cosine similarity (embeddings are normalized)
    scores = np.dot(embeddings, query_emb)
    if mask is not None:
        scores = scores.copy()
        scores[~mask] = -np.inf

    # Get top-k
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    full = get_uniclass_df()
    for idx in top_indices:
        score = float(scores[int(idx)])
        if score >= score_cutoff and np.isfinite(score):
            row = full.iloc[int(idx)]
            results.append((row["code"], score, int(idx)))

    return results


def batch_semantic_search(
    queries: list[str],
    table: str | None = None,
    top_k: int = 10,
) -> list[list[tuple[str, float, int]]]:
    """One model call for many queries; returns per-query top-k lists."""
    embeddings = get_embeddings()
    if embeddings is None:
        return [[] for _ in queries]

    full = get_uniclass_df()
    mask = None
    if table:
        mask = (full["table"] == table).to_numpy()
        if not mask.any():
            return [[] for _ in queries]

    q_embs = embed_queries(list(queries))
    if q_embs is None:
        return [[] for _ in queries]

    scores = q_embs @ embeddings.T
    if mask is not None:
        scores[:, ~mask] = -np.inf

    out: list[list[tuple[str, float, int]]] = []
    for row_scores in scores:
        top = np.argsort(row_scores)[::-1][:top_k]
        hits = []
        for idx in top:
            s = float(row_scores[int(idx)])
            if np.isfinite(s):
                r = full.iloc[int(idx)]
                hits.append((r["code"], s, int(idx)))
        out.append(hits)
    return out


def get_similar_codes(code: str, top_k: int = 10) -> list[tuple[str, float]]:
    """Find codes with similar embeddings to a given code."""
    df = get_uniclass_df()
    idx = df.index[df["code"] == code].tolist()
    if not idx:
        return []

    embeddings = get_embeddings()
    if embeddings is None:
        return []

    query_emb = embeddings[idx[0]]
    scores = np.dot(embeddings, query_emb)

    # Exclude self
    scores[idx[0]] = -1

    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        row = get_uniclass_df().iloc[idx]
        results.append((row["code"], float(scores[idx])))

    return results


if __name__ == "__main__":
    # Quick test
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        print("sentence-transformers not available")
    else:
        print("Computing embeddings...")
        emb = get_embeddings()
        if emb is not None:
            print(f"Embeddings shape: {emb.shape}")

        # Test search
        test_queries = ["air handling unit", "boiler", "fan coil", "vav box", "chiller"]
        for q in test_queries:
            results = semantic_search(q, top_k=3)
            print(f"\nQuery: '{q}'")
            for _code, score, idx in results:
                df = get_uniclass_df()
                row = df.iloc[idx]
                print(f"  {row['code']} ({row['title']}) - score: {score:.3f}")
