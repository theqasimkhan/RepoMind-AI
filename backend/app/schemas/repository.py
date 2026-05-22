from pydantic import BaseModel, Field, HttpUrl, field_validator


class RepositoryAnalyzeRequest(BaseModel):
    repo_url: HttpUrl

    @field_validator("repo_url")
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure the URL is a valid GitHub repository URL."""
        if v.host not in ("github.com", "www.github.com"):
            raise ValueError("Only GitHub repositories are currently supported")
        # Ensure the URL has a path (owner/repo format)
        if not v.path or len(v.path.split("/")) < 2:
            raise ValueError("Invalid GitHub repository URL format")
        return v


class CommitTimelineEntry(BaseModel):
    """Recent commit from a shallow clone; used for time-travel UI (metadata only)."""

    sha: str
    subject: str
    committed_at: int | None = None


class RepositoryAnalyzeResponse(BaseModel):
    repository: str
    repo_clone_url: str | None = Field(
        default=None,
        description="Canonical https://github.com/owner/repo URL used for clone and chat.",
    )
    detected_frontend: list[str]
    detected_backend: list[str]
    detected_databases: list[str]
    devops_signals: list[str]
    dependencies: list[str]
    detected_apis: list[str]
    architecture_patterns: list[str]
    folder_explanations: dict[str, str]
    file_tree: list[str]
    architecture_style: str
    summary: str
    mermaid_diagram: str
    commit_timeline: list[CommitTimelineEntry] = Field(default_factory=list)


class AnalysisJobStartResponse(BaseModel):
    job_id: str
    status: str


class AnalysisJobStatusResponse(BaseModel):
    job_id: str
    repo_url: str | None = None
    user_id: str | None = None
    status: str
    progress: int
    stage: str
    created_at: str | None = None
    updated_at: str | None = None
    error: str | None = None
    result: RepositoryAnalyzeResponse | None = None


class AnalysisJobListResponse(BaseModel):
    jobs: list[AnalysisJobStatusResponse]
