"""Optional gold-set retrieval metrics export (no LLM; FAISS + embeddings only)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.services.retrieval_metrics import metrics_bundle

router = APIRouter(tags=["retrieval-eval"])

_GOLD = Path(__file__).resolve().parent.parent.parent / "eval" / "gold_set.json"
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_VECTOR_STORE = _BACKEND_ROOT.parent / "vector-store"


def _import_vector_index():
    vs = str(_VECTOR_STORE)
    if vs not in sys.path:
        sys.path.insert(0, vs)
    from vector_index import VectorIndex

    return VectorIndex


@router.get("/retrieval/metrics-export")
def export_retrieval_metrics() -> dict:
    """
    Runs the packaged gold set through the same bi-encoder + FAISS path as offline pytest.

    Enable with ``RETRIEVAL_ENABLE_METRICS_ENDPOINT=true``. Disabled by default.
    """
    settings = get_settings()
    if not settings.retrieval_enable_metrics_endpoint:
        raise HTTPException(status_code=404, detail="metrics export disabled")
    if os.environ.get("SKIP_FAISS_EVAL", "").lower() in ("1", "true", "yes"):
        raise HTTPException(status_code=503, detail="SKIP_FAISS_EVAL is set")

    try:
        import faiss  # noqa: F401
        import sentence_transformers  # noqa: F401
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"retrieval stack unavailable: {e}") from e

    VectorIndex = _import_vector_index()

    if not _GOLD.is_file():
        raise HTTPException(status_code=500, detail="gold_set.json missing")

    data = json.loads(_GOLD.read_text(encoding="utf-8"))
    cases_out: list[dict] = []
    mrrs: list[float] = []
    ndcgs: list[float] = []
    recalls: list[float] = []

    for case in data.get("cases", []):
        question = case["question"]
        chunks = case["chunks"]
        k = int(case.get("k", 5))
        gold = case["gold_files"]
        vi = VectorIndex()
        vi.build_index(chunks)
        results = vi.search(question, top_k=k)
        m = metrics_bundle(results, gold, k)
        mrrs.append(m["mrr"])
        ndcgs.append(m[f"ndcg@{k}"])
        recalls.append(m[f"recall@{k}"])
        cases_out.append({"id": case.get("id"), "k": k, "metrics": m})

    n = max(len(mrrs), 1)
    return {
        "description": data.get("description"),
        "embedding_model": data.get("embedding_model"),
        "aggregate": {
            "mean_mrr": sum(mrrs) / n,
            "mean_ndcg": sum(ndcgs) / n,
            "mean_recall": sum(recalls) / n,
            "num_cases": len(mrrs),
        },
        "cases": cases_out,
    }
