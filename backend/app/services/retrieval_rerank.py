"""Optional cross-encoder reranking (lazy import; heavy model on first use)."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_reranker: Any = None
_reranker_model: str | None = None


def reset_reranker_cache_for_tests() -> None:
    global _reranker, _reranker_model
    _reranker = None
    _reranker_model = None


def _get_cross_encoder(model_name: str) -> Any:
    global _reranker, _reranker_model
    if _reranker is not None and _reranker_model == model_name:
        return _reranker
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as e:
        raise RuntimeError(
            "Cross-encoder rerank requires sentence-transformers (install backend requirements)."
        ) from e
    logger.info("Loading cross-encoder reranker model=%s", model_name)
    _reranker = CrossEncoder(model_name)
    _reranker_model = model_name
    return _reranker


def rerank_chunks_cross_encoder(
    query: str,
    chunks: list[dict],
    *,
    top_k: int,
    model_name: str,
    max_doc_chars: int = 8000,
) -> tuple[list[dict], float]:
    """
    Returns (top chunks by cross-encoder score, rerank latency ms).
    """
    if not chunks:
        return [], 0.0
    model = _get_cross_encoder(model_name)
    t0 = time.perf_counter()
    pairs: list[list[str]] = []
    for c in chunks:
        body = str(c.get("content") or "")
        if len(body) > max_doc_chars:
            body = body[:max_doc_chars]
        pairs.append([query, body])
    scores = model.predict(pairs, show_progress_bar=False)
    order = sorted(range(len(chunks)), key=lambda i: float(scores[i]), reverse=True)
    k = min(top_k, len(chunks))
    ranked = [chunks[i] for i in order[:k]]
    ms = (time.perf_counter() - t0) * 1000
    return ranked, ms
