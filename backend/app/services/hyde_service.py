"""Optional HyDE-style query expansion (feature-flagged; mockable in tests)."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


async def maybe_hyde_query(
    question: str,
    *,
    enabled: bool,
    use_llm: bool,
    rag_pipeline: object | None,
) -> tuple[str, bool]:
    """
    Returns ``(query_for_retrieval, hyde_applied)``.

    When disabled, returns the original question. When ``HYDE_EVAL_MOCK`` is set,
    returns a deterministic hypothetical snippet without calling an LLM.
    """
    if not enabled:
        return question, False

    mock = os.environ.get("HYDE_EVAL_MOCK", "").lower() in ("1", "true", "yes")
    if mock:
        extra = os.environ.get(
            "HYDE_EVAL_MOCK_TEXT",
            "Hypothetical excerpt: JWT bearer validation, token signature verification, and key rotation.",
        )
        return f"{question}\n\n{extra}", True

    if not use_llm or rag_pipeline is None:
        return question, False

    hy_fn = getattr(rag_pipeline, "hyde_hypothetical_snippet", None)
    if not callable(hy_fn):
        return question, False

    try:
        hypo = await hy_fn(question)
    except Exception as e:
        logger.warning("HyDE LLM call failed; using raw question: %s", e)
        return question, False

    if not hypo or not str(hypo).strip():
        return question, False

    text = str(hypo).strip()
    return f"{question}\n\n{text}", True
