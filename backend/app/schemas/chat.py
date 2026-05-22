from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class TraceStep(BaseModel):
    """Single span or tool step for deep trace (Phase 3)."""

    name: str
    kind: Literal["span", "tool"]
    latency_ms: float = 0.0
    detail: dict[str, Any] = Field(default_factory=dict)


class ChatQueryRequest(BaseModel):
    repo_url: str
    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("repo_url", mode="before")
    @classmethod
    def normalize_repo_url(cls, v: object) -> str:
        from app.utils.repo_url import normalize_github_repo_url

        return normalize_github_repo_url(str(v).strip())

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Sanitize and validate the question input."""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        # Check for potential injection patterns
        dangerous_patterns = ["<script", "javascript:", "data:", "vbscript:"]
        if any(pattern.lower() in v.lower() for pattern in dangerous_patterns):
            raise ValueError("Question contains invalid characters")
        return v


class SourceCitation(BaseModel):
    """Grounding citation from a retrieved chunk."""

    file_path: str
    chunk_id: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class ChatQueryTrace(BaseModel):
    """Structured trace for observability (also logged server-side)."""

    model_id: str
    top_k: int
    latency_ms: float
    retrieval_latency_ms: float
    llm_latency_ms: float
    num_chunks_in_index: int
    num_chunks_retrieved: int
    embedding_cache_hit: bool = False
    embedding_model: str | None = None
    # Phase 2 — retrieval depth (optional fields default for older clients)
    chunk_strategy: str | None = None
    retrieval_embed_path_prefix: bool = False
    retrieval_fetch_k: int | None = None
    faiss_candidate_count: int | None = None
    rerank_enabled: bool = False
    rerank_latency_ms: float | None = None
    hyde_applied: bool = False
    hyde_latency_ms: float | None = None
    retrieval_query_preview: str | None = Field(
        default=None,
        description="First ~200 chars of the dense-retrieval query (HyDE-expanded or raw).",
    )
    # Phase 3 — agent + deep trace
    trace_steps: list[TraceStep] = Field(default_factory=list)
    agent_enabled: bool = False
    agent_degraded: bool = False
    agent_tool_rounds_used: int = 0


class ChatQueryResponse(BaseModel):
    answer: str
    references: list[str]
    citations: list[SourceCitation] = Field(default_factory=list)
    trace: ChatQueryTrace | None = None
    diagram_mermaid: str | None = Field(
        default=None,
        description="Optional Mermaid from agent diagram tool (bounded hook).",
    )
