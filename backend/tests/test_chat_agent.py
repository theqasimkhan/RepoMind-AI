"""Phase 3 bounded agent: parsing, diagram hook, mock loop (no FAISS / no LLM)."""

import asyncio
import json

from app.services.chat_agent import _mermaid_from_chunk_paths, _parse_tool_json, run_bounded_agent


def test_parse_tool_json_strips_fences():
    raw = '```json\n{"tool": "retrieve", "query": "auth"}\n```'
    p = _parse_tool_json(raw)
    assert p == {"tool": "retrieve", "query": "auth"}


def test_parse_tool_json_invalid():
    assert _parse_tool_json("not json") is None
    assert _parse_tool_json('{"tool": "hack"}') is None


def test_mermaid_from_paths():
    m = _mermaid_from_chunk_paths(["src/app/main.py", "src/lib/x.py"])
    assert "graph LR" in m
    assert "main.py" in m


def test_bounded_agent_mock_retrieve_then_answer(monkeypatch):
    monkeypatch.setenv("CHAT_AGENT_MOCK", "1")
    monkeypatch.setenv(
        "CHAT_AGENT_MOCK_STEPS",
        json.dumps([{"tool": "retrieve", "query": "jwt"}, {"tool": "answer"}]),
    )

    calls: list[str] = []

    def retrieve(q: str):
        calls.append(q)
        return ([{"file_path": "a.py", "content": "x"}], 3, None)

    async def summarize_fn(_chunks):
        raise AssertionError("should not run")

    out = asyncio.run(
        run_bounded_agent(
            question="where is jwt",
            repository="https://github.com/x/y",
            gemini_api_key=None,
            openrouter_api_key=None,
            max_tool_rounds=5,
            max_retrieve_refines=2,
            max_llm_calls=8,
            retrieve=retrieve,
            summarize_fn=summarize_fn,
            initial_query="where is jwt",
            initial_chunks=[{"file_path": "old.py", "content": "old"}],
        )
    )
    assert not out.degraded
    assert "jwt" in calls
    assert out.top_chunks[0]["file_path"] == "a.py"
    names = [s.name for s in out.trace_steps]
    assert "agent.plan" in names
    assert "tool.retrieve" in names
    assert "tool.answer" in names


def test_bounded_agent_planner_failure_degrades(monkeypatch):
    monkeypatch.delenv("CHAT_AGENT_MOCK", raising=False)

    async def summarize_fn(_c):
        return None

    out = asyncio.run(
        run_bounded_agent(
            question="q",
            repository="r",
            gemini_api_key=None,
            openrouter_api_key=None,
            max_tool_rounds=3,
            max_retrieve_refines=1,
            max_llm_calls=5,
            retrieve=lambda q: ([{"file_path": "f.py", "content": "c"}], 1, None),
            summarize_fn=summarize_fn,
            initial_query="q",
            initial_chunks=[{"file_path": "f.py", "content": "c"}],
        )
    )
    assert out.degraded is True


def test_bounded_agent_mock_diagram(monkeypatch):
    monkeypatch.setenv("CHAT_AGENT_MOCK", "1")
    monkeypatch.setenv(
        "CHAT_AGENT_MOCK_STEPS",
        json.dumps([{"tool": "diagram"}, {"tool": "answer"}]),
    )

    async def summarize_fn(_c):
        return None

    out = asyncio.run(
        run_bounded_agent(
            question="architecture",
            repository="r",
            gemini_api_key=None,
            openrouter_api_key=None,
            max_tool_rounds=5,
            max_retrieve_refines=2,
            max_llm_calls=8,
            retrieve=lambda q: (
                [{"file_path": "pkg/a.py", "content": "1"}, {"file_path": "pkg/b.py", "content": "2"}],
                2,
                None,
            ),
            summarize_fn=summarize_fn,
            initial_query="architecture",
            initial_chunks=[{"file_path": "pkg/a.py", "content": "1"}],
        )
    )
    assert out.diagram_mermaid and "graph LR" in out.diagram_mermaid
