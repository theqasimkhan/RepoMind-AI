"""
Offline retrieval metrics with labeled relevance (Phase 2).

Uses normalized file paths for matching. Relevance scores are optional per doc;
default is binary membership in ``gold_files``.
"""

from __future__ import annotations

import math
from typing import Iterable


def _norm_path(p: str) -> str:
    return str(p).replace("\\", "/").strip().lower()


def ranked_paths(results: list[dict]) -> list[str]:
    return [_norm_path(str(c.get("file_path", ""))) for c in results]


def recall_at_k(results: list[dict], gold_files: Iterable[str], k: int) -> float:
    gold = {_norm_path(g) for g in gold_files}
    if not gold:
        return 0.0
    for fp in ranked_paths(results)[:k]:
        if fp in gold:
            return 1.0
    return 0.0


def mrr(results: list[dict], gold_files: Iterable[str]) -> float:
    """Mean reciprocal rank of the first hit (single-query MRR)."""
    gold = {_norm_path(g) for g in gold_files}
    if not gold:
        return 0.0
    for i, fp in enumerate(ranked_paths(results), start=1):
        if fp in gold:
            return 1.0 / i
    return 0.0


def dcg_at_k(relevance_scores: list[float], k: int) -> float:
    s = 0.0
    for i, rel in enumerate(relevance_scores[:k], start=1):
        s += (2**rel - 1) / math.log2(i + 1)
    return s


def ndcg_at_k(results: list[dict], gold_files: Iterable[str], k: int) -> float:
    """
    nDCG@k with binary relevance (1 if path in gold set, else 0).
    Multiple gold files each count as relevant.
    """
    gold = {_norm_path(g) for g in gold_files}
    if not gold:
        return 0.0
    rels = [1.0 if fp in gold else 0.0 for fp in ranked_paths(results)]
    ideal = sorted(rels, reverse=True)
    dcg = dcg_at_k(rels, k)
    idcg = dcg_at_k(ideal, k)
    if idcg <= 0:
        return 0.0
    return dcg / idcg


def metrics_bundle(results: list[dict], gold_files: list[str], k: int) -> dict[str, float]:
    return {
        f"recall@{k}": recall_at_k(results, gold_files, k),
        "mrr": mrr(results, gold_files),
        f"ndcg@{k}": ndcg_at_k(results, gold_files, k),
    }
