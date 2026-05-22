"""Unit tests for offline retrieval metrics (no FAISS)."""

from app.services.retrieval_metrics import mrr, ndcg_at_k, recall_at_k


def test_recall_at_k_binary():
    results = [
        {"file_path": "a.py"},
        {"file_path": "b.py"},
    ]
    assert recall_at_k(results, ["b.py"], k=2) == 1.0
    assert recall_at_k(results, ["c.py"], k=2) == 0.0


def test_mrr_first_rank():
    results = [{"file_path": "x.py"}, {"file_path": "gold.py"}]
    assert mrr(results, ["gold.py"]) == 0.5


def test_mrr_miss():
    assert mrr([{"file_path": "a.py"}], ["b.py"]) == 0.0


def test_ndcg_perfect_vs_partial():
    gold = ["b.py", "a.py"]
    perfect = [{"file_path": "b.py"}, {"file_path": "a.py"}, {"file_path": "c.py"}]
    partial = [{"file_path": "c.py"}, {"file_path": "b.py"}, {"file_path": "a.py"}]
    assert ndcg_at_k(perfect, gold, k=3) == 1.0
    assert ndcg_at_k(partial, gold, k=3) < 1.0
