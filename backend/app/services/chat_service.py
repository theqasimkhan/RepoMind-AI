import json
import logging
import sys
import time
from pathlib import Path

# Add sibling directories to sys.path so we can import from them
backend_dir = Path(__file__).resolve().parent.parent.parent
project_root = backend_dir.parent
ai_engine_dir = project_root / "ai_engine"
vector_store_dir = project_root / "vector-store"

for path in [project_root, ai_engine_dir, vector_store_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ai_engine.rag_pipeline import RagPipeline, RagContext
from app.schemas.chat import ChatQueryResponse, ChatQueryTrace, SourceCitation, TraceStep
from app.services.chat_agent import run_bounded_agent
from app.services.embedding_cache import (
    compute_cache_stem,
    compute_chunk_set_fingerprint,
    load_or_build_embeddings,
    resolve_cache_dir,
)
from app.services.hyde_service import maybe_hyde_query
from app.services.repository_service import RepositoryAnalysisService, analysis_job_manager
from app.services.retrieval_rerank import rerank_chunks_cross_encoder
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _import_vector_index():
    try:
        from vector_index import VectorIndex
    except ImportError:
        vs = Path(__file__).resolve().parent.parent.parent.parent / "vector-store"
        if str(vs) not in sys.path:
            sys.path.insert(0, str(vs))
        from vector_index import VectorIndex

    return VectorIndex


def _resolve_model_id(settings) -> str:
    if settings.openrouter_api_key:
        return "google/gemini-2.5-flash"
    if settings.gemini_api_key:
        return "gemini-2.5-flash"
    return "none"


def _citations_from_chunks(top_chunks: list[dict]) -> list[SourceCitation]:
    out: list[SourceCitation] = []
    for chunk in top_chunks:
        fp = str(chunk.get("file_path") or "")
        idx = chunk.get("chunk_index", 0)
        cid = f"{fp}#c{idx}" if fp else None
        sl = chunk.get("start_line")
        el = chunk.get("end_line")
        out.append(
            SourceCitation(
                file_path=fp,
                chunk_id=cid,
                start_line=int(sl) if sl is not None else None,
                end_line=int(el) if el is not None else None,
            )
        )
    return out


def _faiss_search(
    vector_index,
    retrieval_query: str,
    top_k: int,
    rerank_on: bool,
    num_in_index: int,
    settings,
) -> tuple[list[dict], list[dict], float | None]:
    first_k: int | None = None
    if rerank_on:
        first_k = min(max(settings.retrieval_fetch_k, top_k), num_in_index)

    candidates = vector_index.search(
        retrieval_query,
        top_k=top_k,
        first_stage_k=first_k,
    )
    rerank_ms: float | None = None
    if rerank_on and len(candidates) > 0:
        try:
            top_chunks, rerank_ms = rerank_chunks_cross_encoder(
                retrieval_query,
                candidates,
                top_k=top_k,
                model_name=settings.retrieval_rerank_model,
            )
        except Exception as e:
            logger.warning("Rerank failed; using bi-encoder order: %s", e)
            top_chunks = candidates[:top_k]
            rerank_ms = None
    else:
        top_chunks = candidates[:top_k]

    return top_chunks, candidates, rerank_ms


class RepositoryChatService:
    async def ask(self, repo_url: str, question: str) -> ChatQueryResponse:
        t0 = time.perf_counter()
        settings = get_settings()
        top_k = settings.chat_top_k
        trace_steps: list[TraceStep] = []

        chunks = analysis_job_manager.get_retrieval_chunks(repo_url=repo_url, limit=250)
        job_id = analysis_job_manager.get_latest_completed_job_id(repo_url) if chunks else None

        if not chunks:
            _, chunks = await RepositoryAnalysisService().analyze_with_chunks(repo_url)
            job_id = None

        num_in_index = len(chunks)

        pipeline = RagPipeline(
            gemini_api_key=settings.gemini_api_key,
            openrouter_api_key=settings.openrouter_api_key,
        )

        hyde_t0 = time.perf_counter()
        retrieval_query, hyde_applied = await maybe_hyde_query(
            question,
            enabled=settings.retrieval_enable_hyde,
            use_llm=settings.retrieval_hyde_use_llm,
            rag_pipeline=pipeline,
        )
        hyde_ms = (time.perf_counter() - hyde_t0) * 1000
        trace_steps.append(
            TraceStep(
                name="retrieval.hyde",
                kind="span",
                latency_ms=round(hyde_ms, 2),
                detail={"applied": hyde_applied},
            )
        )

        embed_t0 = time.perf_counter()
        VectorIndex = _import_vector_index()
        vector_index = VectorIndex()
        fingerprint = compute_chunk_set_fingerprint(chunks)
        embed_variant = f"pfx={int(settings.retrieval_embed_path_prefix)}"
        stem = compute_cache_stem(
            repo_url,
            job_id or "ephemeral",
            fingerprint,
            vector_index.model_name,
            embedding_variant=embed_variant,
        )
        cache_dir = resolve_cache_dir(settings.vector_cache_dir, backend_dir)
        max_bytes = max(0, settings.vector_cache_max_mb * 1024 * 1024)

        embeddings, cache_hit = load_or_build_embeddings(
            vector_index=vector_index,
            chunks=chunks,
            cache_dir=cache_dir,
            stem=stem,
            ttl_seconds=settings.vector_cache_ttl_seconds,
            max_total_bytes=max_bytes,
            embed_path_prefix=settings.retrieval_embed_path_prefix,
        )
        vector_index.set_index_from_embeddings(chunks, embeddings)
        embed_ms = (time.perf_counter() - embed_t0) * 1000
        trace_steps.append(
            TraceStep(
                name="embedding.cache",
                kind="span",
                latency_ms=round(embed_ms, 2),
                detail={"hit": cache_hit, "model": vector_index.model_name},
            )
        )

        rerank_on = settings.retrieval_enable_rerank and num_in_index > 0
        effective_fetch_k: int | None = None
        if rerank_on:
            effective_fetch_k = min(max(settings.retrieval_fetch_k, top_k), num_in_index)

        retrieval_t0 = time.perf_counter()
        top_chunks, candidates, rerank_ms = _faiss_search(
            vector_index,
            retrieval_query,
            top_k,
            rerank_on,
            num_in_index,
            settings,
        )
        retrieval_ms = (time.perf_counter() - retrieval_t0) * 1000
        trace_steps.append(
            TraceStep(
                name="retrieval.faiss",
                kind="span",
                latency_ms=round(retrieval_ms, 2),
                detail={
                    "candidates": len(candidates),
                    "chunks_used": len(top_chunks),
                    "rerank_ms": rerank_ms,
                    "rerank_enabled": rerank_on and rerank_ms is not None,
                },
            )
        )

        initial_top_chunks = list(top_chunks)
        diagram_mermaid: str | None = None
        auxiliary_notes: list[str] = []
        agent_enabled = bool(
            settings.chat_agent_enabled
            and (settings.gemini_api_key or settings.openrouter_api_key)
        )
        agent_degraded = False
        agent_tool_rounds = 0

        if agent_enabled:
            try:

                def retrieve_fn(q: str) -> tuple[list[dict], int, float | None]:
                    return _faiss_search(vector_index, q, top_k, rerank_on, num_in_index, settings)

                async def summarize_fn(chs: list[dict]) -> str | None:
                    blocks = [
                        f"File: {c.get('file_path', '')}\n{c.get('content', '')[:4000]}" for c in chs[:10]
                    ]
                    return await pipeline.summarize_snippets(blocks)

                agent_out = await run_bounded_agent(
                    question=question,
                    repository=repo_url,
                    gemini_api_key=settings.gemini_api_key,
                    openrouter_api_key=settings.openrouter_api_key,
                    max_tool_rounds=settings.chat_agent_max_tool_rounds,
                    max_retrieve_refines=settings.chat_agent_max_retrieve_refines,
                    max_llm_calls=settings.chat_agent_max_llm_calls,
                    retrieve=retrieve_fn,
                    summarize_fn=summarize_fn,
                    initial_query=retrieval_query,
                    initial_chunks=initial_top_chunks,
                )
                trace_steps.extend(agent_out.trace_steps)
                agent_tool_rounds = agent_out.tool_rounds_used
                if agent_out.degraded:
                    agent_degraded = True
                    top_chunks = list(initial_top_chunks)
                    auxiliary_notes = []
                    diagram_mermaid = None
                    logger.warning("Chat agent degraded to initial retrieval (planner failure)")
                else:
                    top_chunks = agent_out.top_chunks
                    auxiliary_notes = list(agent_out.auxiliary_notes)
                    diagram_mermaid = agent_out.diagram_mermaid
            except Exception as e:
                agent_degraded = True
                top_chunks = list(initial_top_chunks)
                auxiliary_notes = []
                diagram_mermaid = None
                trace_steps.append(
                    TraceStep(
                        name="agent.error",
                        kind="span",
                        latency_ms=0.0,
                        detail={"error": str(e)[:500]},
                    )
                )
                logger.warning("Chat agent failed; single-shot RAG: %s", e)
        else:
            top_chunks = initial_top_chunks

        references = [str(c["file_path"]) for c in top_chunks]
        unique_references = list(dict.fromkeys(references))

        formatted_chunks = [
            f"File: {chunk['file_path']}\nContent:\n{chunk['content']}" for chunk in top_chunks
        ]
        if auxiliary_notes:
            formatted_chunks.append("Agent notes:\n" + "\n\n".join(auxiliary_notes))

        context = RagContext(repository=repo_url, question=question, retrieved_chunks=formatted_chunks)

        llm_t0 = time.perf_counter()
        answer = await pipeline.answer(context)
        llm_ms = (time.perf_counter() - llm_t0) * 1000
        trace_steps.append(
            TraceStep(
                name="llm.answer",
                kind="span",
                latency_ms=round(llm_ms, 2),
                detail={"agent": agent_enabled},
            )
        )

        total_ms = (time.perf_counter() - t0) * 1000
        model_id = _resolve_model_id(settings)

        q_preview = retrieval_query if len(retrieval_query) <= 200 else retrieval_query[:200] + "…"

        trace = ChatQueryTrace(
            model_id=model_id,
            top_k=top_k,
            latency_ms=round(total_ms, 2),
            retrieval_latency_ms=round(retrieval_ms, 2),
            llm_latency_ms=round(llm_ms, 2),
            num_chunks_in_index=num_in_index,
            num_chunks_retrieved=len(top_chunks),
            embedding_cache_hit=cache_hit,
            embedding_model=vector_index.model_name,
            chunk_strategy=settings.retrieval_chunk_strategy,
            retrieval_embed_path_prefix=settings.retrieval_embed_path_prefix,
            retrieval_fetch_k=effective_fetch_k,
            faiss_candidate_count=len(candidates),
            rerank_enabled=rerank_on and rerank_ms is not None,
            rerank_latency_ms=round(rerank_ms, 2) if rerank_ms is not None else None,
            hyde_applied=hyde_applied,
            hyde_latency_ms=round(hyde_ms, 2) if settings.retrieval_enable_hyde else None,
            retrieval_query_preview=q_preview,
            trace_steps=trace_steps,
            agent_enabled=agent_enabled,
            agent_degraded=agent_degraded,
            agent_tool_rounds_used=agent_tool_rounds,
        )

        logger.info(
            json.dumps(
                {
                    "event": "chat_query",
                    "repo_url": repo_url,
                    "question_len": len(question),
                    "trace": trace.model_dump(),
                },
                default=str,
            )
        )

        citations = _citations_from_chunks(top_chunks)

        return ChatQueryResponse(
            answer=answer,
            references=unique_references[:top_k],
            citations=citations,
            trace=trace,
            diagram_mermaid=diagram_mermaid,
        )
