"""
Celery tasks — Phase 2.
analyze_repository_task: runs a full repo analysis job synchronously inside a Celery worker.
"""
import asyncio

from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="repomind.analyze_repository", max_retries=2)
def analyze_repository_task(self, job_id: str) -> dict:
    """
    Run repository analysis for the given job_id.
    Delegates to AnalysisJobManager._run_job via asyncio.run().
    """
    from app.services.repository_service import analysis_job_manager  # avoid circular at import time

    try:
        asyncio.run(analysis_job_manager._run_job(job_id))
        return {"job_id": job_id, "status": "completed"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
