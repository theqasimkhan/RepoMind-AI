"""HyDE query expansion (mocked; no LLM)."""

import asyncio

from app.services.hyde_service import maybe_hyde_query


def test_hyde_mock_env_expands_without_llm(monkeypatch):
    monkeypatch.setenv("HYDE_EVAL_MOCK", "1")
    monkeypatch.setenv("HYDE_EVAL_MOCK_TEXT", "def verify_token(): pass")
    q, used = asyncio.run(
        maybe_hyde_query(
            "Where is JWT verified?",
            enabled=True,
            use_llm=False,
            rag_pipeline=None,
        )
    )
    assert used is True
    assert "verify_token" in q


def test_hyde_disabled_returns_original(monkeypatch):
    monkeypatch.delenv("HYDE_EVAL_MOCK", raising=False)
    q, used = asyncio.run(
        maybe_hyde_query(
            "plain",
            enabled=False,
            use_llm=True,
            rag_pipeline=None,
        )
    )
    assert q == "plain" and used is False
