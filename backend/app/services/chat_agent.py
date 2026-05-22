"""
Phase 3 — bounded tool-using chat agent (retrieve, summarize, diagram).

Planner LLM chooses one tool per round; hard caps prevent unbounded loops.
On planner/parse failure, caller should fall back to single-shot RAG.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.schemas.chat import TraceStep

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """Mutable state while the agent loop runs."""

    top_chunks: list[dict]
    auxiliary_notes: list[str] = field(default_factory=list)
    retrieve_refines_used: int = 0
    summarize_used: int = 0
    diagram_used: int = 0
    tool_rounds: int = 0
    llm_calls: int = 0


@dataclass
class BoundedAgentResult:
    top_chunks: list[dict]
    auxiliary_notes: list[str]
    trace_steps: list[TraceStep]
    degraded: bool
    diagram_mermaid: str | None
    tool_rounds_used: int


def _mermaid_from_chunk_paths(paths: list[str], max_nodes: int = 8) -> str:
    """Deterministic diagram hook from retrieved file paths (no LLM)."""
    clean: list[str] = []
    for p in paths:
        s = (p or "").replace('"', "'").strip()
        if not s:
            continue
        short = s.split("/")[-1][:40] or s[:40]
        label = short
        if label not in clean:
            clean.append(label)
        if len(clean) >= max_nodes:
            break
    if not clean:
        return "graph TD\nA[No files] --> B[Refine query]"
    lines = ["graph LR"]
    prev = None
    for i, label in enumerate(clean):
        nid = f"N{i}"
        safe = re.sub(r"[^\w\-./ ]", "", label)[:48]
        lines.append(f'{nid}["{safe}"]')
        if prev is not None:
            lines.append(f"  {prev} --> {nid}")
        prev = nid
    return "\n".join(lines)


def _parse_tool_json(raw: str) -> dict[str, Any] | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    tool = data.get("tool")
    if tool not in ("retrieve", "summarize", "diagram", "answer"):
        return None
    return data


async def _invoke_planner_llm(
    *,
    gemini_api_key: str | None,
    openrouter_api_key: str | None,
    system: str,
    human: str,
) -> str | None:
    if openrouter_api_key:
        llm = ChatOpenAI(
            model="google/gemini-2.5-flash",
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
        )
    elif gemini_api_key:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,
            temperature=0.1,
        )
    else:
        return None
    try:
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        text = resp.content if isinstance(resp.content, str) else str(resp.content)
        return text.strip() or None
    except Exception as e:
        logger.warning("Agent planner LLM failed: %s", e)
        return None


def _mock_plan_steps() -> list[dict[str, Any]]:
    raw = os.environ.get("CHAT_AGENT_MOCK_STEPS", "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
        except json.JSONDecodeError:
            pass
    return [{"tool": "answer"}]


async def run_bounded_agent(
    *,
    question: str,
    repository: str,
    gemini_api_key: str | None,
    openrouter_api_key: str | None,
    max_tool_rounds: int,
    max_retrieve_refines: int,
    max_llm_calls: int,
    retrieve: Callable[[str], tuple[list[dict], int, float | None]],
    summarize_fn: Callable[[list[dict]], Awaitable[str | None]],
    initial_query: str,
    initial_chunks: list[dict],
) -> BoundedAgentResult:
    """
    `retrieve(query)` returns (top_chunks, faiss_candidate_count, rerank_latency_ms or None).
    Initial retrieval is logged by the caller as a span; this loop records planner/tool steps only.
    """
    steps: list[TraceStep] = []
    state = AgentState(top_chunks=list(initial_chunks))
    degraded = False
    diagram_mermaid: str | None = None

    mock_mode = os.environ.get("CHAT_AGENT_MOCK", "").lower() in ("1", "true", "yes")
    plan_queue: list[dict[str, Any]] = _mock_plan_steps() if mock_mode else []

    system = (
        "You are a bounded repository assistant planner. Output a single JSON object only, no markdown. "
        'Schema: {"tool":"retrieve"|"summarize"|"diagram"|"answer","query":string optional,'
        '"rationale":string optional}. '
        "Rules: use retrieve only to search again with a NEW short query (max 200 chars). "
        "summarize: condense current retrieved snippets. diagram: high-level file flow from current chunks. "
        "answer: stop using tools; the system will write the final user-facing answer. "
        "Prefer answer when current chunks likely suffice."
    )

    round_idx = 0
    while round_idx < max_tool_rounds and state.llm_calls < max_llm_calls:
        round_idx += 1
        obs_lines = [
            f"User question: {question}",
            f"Retrieved files: {[c.get('file_path') for c in state.top_chunks[:8]]}",
        ]
        if state.auxiliary_notes:
            obs_lines.append("Notes from tools:\n" + "\n".join(state.auxiliary_notes[-6:]))
        human = (
            "\n".join(obs_lines)
            + f"\n\nRetrieve refines left: {max(0, max_retrieve_refines - state.retrieve_refines_used)}. "
            f"Round {round_idx}/{max_tool_rounds}."
        )

        t_plan = time.perf_counter()
        if mock_mode:
            action = plan_queue.pop(0) if plan_queue else {"tool": "answer"}
            raw = json.dumps(action)
            state.llm_calls += 1
        else:
            raw = await _invoke_planner_llm(
                gemini_api_key=gemini_api_key,
                openrouter_api_key=openrouter_api_key,
                system=system,
                human=human,
            )
            state.llm_calls += 1
            if raw is None:
                degraded = True
                break
            action = _parse_tool_json(raw)
            if action is None:
                degraded = True
                break

        tool = action.get("tool")
        steps.append(
            TraceStep(
                name="agent.plan",
                kind="span",
                latency_ms=round((time.perf_counter() - t_plan) * 1000, 2),
                detail={"tool": tool, "raw_preview": (raw or "")[:240]},
            )
        )

        if tool == "answer":
            steps.append(
                TraceStep(
                    name="tool.answer",
                    kind="tool",
                    latency_ms=0.0,
                    detail={"stop": True},
                )
            )
            break

        if state.tool_rounds >= max_tool_rounds:
            degraded = True
            break

        t_tool = time.perf_counter()

        if tool == "retrieve":
            if state.retrieve_refines_used >= max_retrieve_refines:
                state.auxiliary_notes.append("(retrieve skipped: refine budget exhausted)")
                steps.append(
                    TraceStep(
                        name="tool.retrieve",
                        kind="tool",
                        latency_ms=round((time.perf_counter() - t_tool) * 1000, 2),
                        detail={"skipped": True, "reason": "max_retrieve_refines"},
                    )
                )
                continue
            q = str(action.get("query") or "")[:200].strip() or initial_query
            state.retrieve_refines_used += 1
            top, faiss_n, rr_ms = retrieve(q)
            state.top_chunks = top
            state.tool_rounds += 1
            steps.append(
                TraceStep(
                    name="tool.retrieve",
                    kind="tool",
                    latency_ms=round((time.perf_counter() - t_tool) * 1000, 2),
                    detail={
                        "query_preview": q[:120],
                        "chunks": len(top),
                        "faiss_candidate_count": faiss_n,
                        "rerank_latency_ms": rr_ms,
                    },
                )
            )

        elif tool == "summarize":
            if state.summarize_used >= 1:
                state.auxiliary_notes.append("(summarize skipped: already used)")
                steps.append(
                    TraceStep(
                        name="tool.summarize",
                        kind="tool",
                        latency_ms=round((time.perf_counter() - t_tool) * 1000, 2),
                        detail={"skipped": True},
                    )
                )
                continue
            state.summarize_used += 1
            if state.llm_calls >= max_llm_calls:
                degraded = True
                break
            summary = await summarize_fn(state.top_chunks)
            state.llm_calls += 1
            state.tool_rounds += 1
            if summary:
                state.auxiliary_notes.append(f"Summary:\n{summary[:2000]}")
            steps.append(
                TraceStep(
                    name="tool.summarize",
                    kind="tool",
                    latency_ms=round((time.perf_counter() - t_tool) * 1000, 2),
                    detail={"chars": len(summary or "")},
                )
            )

        elif tool == "diagram":
            if state.diagram_used >= 1:
                steps.append(
                    TraceStep(
                        name="tool.diagram",
                        kind="tool",
                        latency_ms=round((time.perf_counter() - t_tool) * 1000, 2),
                        detail={"skipped": True},
                    )
                )
                continue
            state.diagram_used += 1
            paths = [str(c.get("file_path") or "") for c in state.top_chunks]
            diagram_mermaid = _mermaid_from_chunk_paths(paths)
            state.tool_rounds += 1
            state.auxiliary_notes.append(f"Architecture sketch (Mermaid):\n{diagram_mermaid}")
            steps.append(
                TraceStep(
                    name="tool.diagram",
                    kind="tool",
                    latency_ms=round((time.perf_counter() - t_tool) * 1000, 2),
                    detail={"nodes": min(8, len(paths))},
                )
            )

    return BoundedAgentResult(
        top_chunks=state.top_chunks,
        auxiliary_notes=state.auxiliary_notes,
        trace_steps=steps,
        degraded=degraded,
        diagram_mermaid=diagram_mermaid,
        tool_rounds_used=state.tool_rounds,
    )
