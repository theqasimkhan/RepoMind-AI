import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RetrievalChunkStrategy = Literal["fixed", "structure_aware"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="RepoMind API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    sqlite_db_path: str = Field(default="repomind.db", alias="SQLITE_DB_PATH")

    # Phase 2 — Auth / JWT
    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=10080, alias="JWT_EXPIRE_MINUTES")

    # Phase 2 — GitHub OAuth
    github_client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", alias="GITHUB_CLIENT_SECRET")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    # Phase 2 — Celery / Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Phase 1 — Embedding / FAISS disk cache (relative paths resolve under backend/)
    vector_cache_dir: str = Field(default=".cache/repomind/vectors", alias="VECTOR_CACHE_DIR")
    vector_cache_ttl_seconds: int = Field(default=86400 * 7, alias="VECTOR_CACHE_TTL_SECONDS")
    vector_cache_max_mb: int = Field(default=512, alias="VECTOR_CACHE_MAX_MB")

    # Phase 2 (roadmap) — Retrieval depth: chunking, HyDE, optional rerank (see docs/ADVANCEMENT_PHASES.md)
    retrieval_chunk_strategy: RetrievalChunkStrategy = Field(
        default="fixed", alias="RETRIEVAL_CHUNK_STRATEGY"
    )
    retrieval_chunk_size: int = Field(default=1200, alias="RETRIEVAL_CHUNK_SIZE", ge=200, le=16000)
    retrieval_chunk_overlap: int = Field(default=150, alias="RETRIEVAL_CHUNK_OVERLAP", ge=0, le=2000)
    retrieval_max_chunks_per_file: int = Field(
        default=8, alias="RETRIEVAL_MAX_CHUNKS_PER_FILE", ge=1, le=64
    )
    retrieval_embed_path_prefix: bool = Field(default=False, alias="RETRIEVAL_EMBED_PATH_PREFIX")
    retrieval_fetch_k: int = Field(default=24, alias="RETRIEVAL_FETCH_K", ge=1, le=200)
    retrieval_enable_rerank: bool = Field(default=False, alias="RETRIEVAL_ENABLE_RERANK")
    retrieval_rerank_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="RETRIEVAL_RERANK_MODEL"
    )
    retrieval_enable_hyde: bool = Field(default=False, alias="RETRIEVAL_ENABLE_HYDE")
    retrieval_hyde_use_llm: bool = Field(default=True, alias="RETRIEVAL_HYDE_USE_LLM")
    chat_top_k: int = Field(default=6, alias="CHAT_TOP_K", ge=1, le=50)
    retrieval_enable_metrics_endpoint: bool = Field(
        default=False, alias="RETRIEVAL_ENABLE_METRICS_ENDPOINT"
    )

    # Phase 3 — bounded tool agent (see docs/ADVANCEMENT_PHASES.md)
    chat_agent_enabled: bool = Field(default=False, alias="CHAT_AGENT_ENABLED")
    chat_agent_max_tool_rounds: int = Field(
        default=5, alias="CHAT_AGENT_MAX_TOOL_ROUNDS", ge=1, le=20
    )
    chat_agent_max_retrieve_refines: int = Field(
        default=2, alias="CHAT_AGENT_MAX_RETRIEVE_REFINES", ge=0, le=10
    )
    chat_agent_max_llm_calls: int = Field(
        default=8,
        alias="CHAT_AGENT_MAX_LLM_CALLS",
        ge=2,
        le=32,
        description="Planner + summarize LLM calls during agent loop (final answer is separate).",
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or v in ("change-me", "", "secret", "password"):
            raise ValueError(
                "JWT_SECRET must be set to a strong random value. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
