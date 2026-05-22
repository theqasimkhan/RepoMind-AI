from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.repository import (
    AnalysisJobListResponse,
    AnalysisJobStartResponse,
    AnalysisJobStatusResponse,
    RepositoryAnalyzeRequest,
    RepositoryAnalyzeResponse,
)
from app.services.repository_service import RepositoryAnalysisService, analysis_job_manager
from app.core.dependencies import get_optional_user
from app.models.user import User

router = APIRouter(prefix="/repositories", tags=["repositories"])
limiter = Limiter(key_func=get_remote_address)


def get_repository_analysis_service() -> RepositoryAnalysisService:
    return RepositoryAnalysisService()


@router.post("/analyze", response_model=RepositoryAnalyzeResponse)
@limiter.limit("5/minute")
async def analyze_repository(
    request: Request,
    payload: RepositoryAnalyzeRequest,
    service: RepositoryAnalysisService = Depends(get_repository_analysis_service),
) -> RepositoryAnalyzeResponse:
    try:
        return await service.analyze(str(payload.repo_url))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze/async", response_model=AnalysisJobStartResponse)
@limiter.limit("5/minute")
async def start_repository_analysis_job(
    request: Request,
    payload: RepositoryAnalyzeRequest,
    user: Optional[User] = Depends(get_optional_user),
) -> AnalysisJobStartResponse:
    user_id = user.id if user else None
    job_id = analysis_job_manager.create_job(str(payload.repo_url), user_id=user_id)
    return AnalysisJobStartResponse(job_id=job_id, status="queued")


@router.get("/analyze/async/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_repository_analysis_job(job_id: str) -> AnalysisJobStatusResponse:
    job = analysis_job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalysisJobStatusResponse(**job)


@router.get("/analyze/async", response_model=AnalysisJobListResponse)
async def list_repository_analysis_jobs(
    limit: int = 20,
    user: Optional[User] = Depends(get_optional_user),
) -> AnalysisJobListResponse:
    user_id = user.id if user else None
    jobs = analysis_job_manager.list_recent_jobs(limit=limit, user_id=user_id)
    return AnalysisJobListResponse(jobs=[AnalysisJobStatusResponse(**job) for job in jobs])


@router.get("/analysis/latest", response_model=RepositoryAnalyzeResponse)
async def get_latest_repository_analysis(repo_url: str) -> RepositoryAnalyzeResponse:
    """Return the most recent completed analysis snapshot for a repository URL (for Galaxy / chat UI)."""
    from app.utils.repo_url import normalize_github_repo_url

    try:
        canon = normalize_github_repo_url(repo_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = analysis_job_manager.get_latest_completed_analysis(canon)
    if not result:
        raise HTTPException(status_code=404, detail="No completed analysis found for this repository URL")
    return result
