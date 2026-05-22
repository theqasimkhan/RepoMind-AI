"""
Offline retrieval eval: Recall@k against gold file paths (no paid LLM).

Skip with: SKIP_FAISS_EVAL=1
Requires: faiss-cpu, sentence-transformers (downloads model on first run).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.services.retrieval_metrics import metrics_bundle

_GOLD_PATH = Path(__file__).resolve().parent.parent / "eval" / "gold_set.json"


pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_FAISS_EVAL", "").lower() in ("1", "true", "yes"),
    reason="SKIP_FAISS_EVAL is set",
)


@pytest.fixture(scope="module")
def gold_cases():
    data = json.loads(_GOLD_PATH.read_text(encoding="utf-8"))
    return data["cases"]


def test_gold_file_exists():
    assert _GOLD_PATH.is_file(), f"missing gold set at {_GOLD_PATH}"


def test_recall_at_k_on_synthetic_corpus(gold_cases):
    pytest.importorskip("faiss")
    pytest.importorskip("sentence_transformers")
    from vector_index import VectorIndex

    for case in gold_cases:
        question = case["question"]
        chunks = case["chunks"]
        k = int(case.get("k", 5))
        gold = case["gold_files"]

        vi = VectorIndex()
        vi.build_index(chunks)
        results = vi.search(question, top_k=k)
        assert results, f"no retrieval results for case {case['id']}"
        m = metrics_bundle(results, gold, k)
        assert m[f"recall@{k}"] >= 1.0, (
            f"Recall@{k} failed for {case['id']}: got {[c.get('file_path') for c in results[:k]]}, "
            f"expected one of {gold}; metrics={m}"
        )
        assert m["mrr"] > 0, f"MRR failed for {case['id']}: metrics={m}"
        assert m[f"ndcg@{k}"] > 0, f"nDCG@{k} failed for {case['id']}: metrics={m}"


def test_metrics_bundle_deterministic_ordering():
    results = [{"file_path": "z.py"}, {"file_path": "a.py"}]
    gold = ["a.py"]
    m = metrics_bundle(results, gold, k=2)
    assert m["mrr"] == 0.5
    assert 0 < m["ndcg@2"] < 1.0
