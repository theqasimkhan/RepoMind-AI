import json
import logging
import sqlite3
from contextlib import contextmanager
from typing import Any

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class AnalysisJobsRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            pool_pre_ping=True,
        )

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with automatic cleanup."""
        conn = self._engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._get_connection() as connection:
            connection.execute(
                text("""
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    job_id TEXT PRIMARY KEY,
                    repo_url TEXT NOT NULL,
                    user_id TEXT,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    error TEXT,
                    result_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            )
            connection.execute(
                text("""
                CREATE TABLE IF NOT EXISTS analysis_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    start_line INTEGER,
                    end_line INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(job_id) REFERENCES analysis_jobs(job_id)
                )
                """)
            )
            connection.execute(
                text("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    github_id INTEGER UNIQUE NOT NULL,
                    login TEXT NOT NULL,
                    name TEXT,
                    email TEXT,
                    avatar_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            )
            connection.commit()

    def create_job(self, job_id: str, repo_url: str, user_id: str | None = None) -> None:
        with self._get_connection() as connection:
            connection.execute(
                text(
                    "INSERT INTO analysis_jobs (job_id, repo_url, user_id, status, progress, stage) "
                    "VALUES (:job_id, :repo_url, :user_id, :status, :progress, :stage)"
                ),
                {
                    "job_id": job_id,
                    "repo_url": repo_url,
                    "user_id": user_id,
                    "status": "queued",
                    "progress": 0,
                    "stage": "Queued",
                },
            )
            connection.commit()

    def update_job(
        self,
        job_id: str,
        *,
        status: str,
        progress: int,
        stage: str,
        error: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        result_json = json.dumps(result) if result else None
        with self._get_connection() as connection:
            connection.execute(
                text(
                    """
                UPDATE analysis_jobs
                SET status = :status, progress = :progress, stage = :stage, error = :error, result_json = :result_json,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id
                """
                ),
                {
                    "status": status,
                    "progress": progress,
                    "stage": stage,
                    "error": error,
                    "result_json": result_json,
                    "job_id": job_id,
                },
            )
            connection.commit()

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._get_connection() as connection:
            row = connection.execute(
                text(
                    """
                SELECT job_id, repo_url, user_id, status, progress, stage, error, result_json, created_at, updated_at
                FROM analysis_jobs
                WHERE job_id = :job_id
                """
                ),
                {"job_id": job_id},
            ).fetchone()
        if not row:
            return None
        result = json.loads(row[7]) if row[7] else None
        return {
            "job_id": row[0],
            "repo_url": row[1],
            "user_id": row[2],
            "status": row[3],
            "progress": row[4],
            "stage": row[5],
            "error": row[6],
            "result": result,
            "created_at": row[8],
            "updated_at": row[9],
        }

    def list_recent_jobs(
        self, limit: int = 20, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self._get_connection() as connection:
            if user_id:
                rows = connection.execute(
                    text(
                        """
                    SELECT job_id, repo_url, user_id, status, progress, stage, error, result_json, created_at, updated_at
                    FROM analysis_jobs
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                    LIMIT :limit
                    """
                    ),
                    {"user_id": user_id, "limit": limit},
                ).fetchall()
            else:
                rows = connection.execute(
                    text(
                        """
                    SELECT job_id, repo_url, user_id, status, progress, stage, error, result_json, created_at, updated_at
                    FROM analysis_jobs
                    ORDER BY updated_at DESC
                    LIMIT :limit
                    """
                    ),
                    {"limit": limit},
                ).fetchall()
        jobs: list[dict[str, Any]] = []
        for row in rows:
            jobs.append(
                {
                    "job_id": row[0],
                    "repo_url": row[1],
                    "user_id": row[2],
                    "status": row[3],
                    "progress": row[4],
                    "stage": row[5],
                    "error": row[6],
                    "result": json.loads(row[7]) if row[7] else None,
                    "created_at": row[8],
                    "updated_at": row[9],
                }
            )
        return jobs

    def get_repo_url(self, job_id: str) -> str | None:
        with self._get_connection() as connection:
            row = connection.execute(
                text("SELECT repo_url FROM analysis_jobs WHERE job_id = :job_id"),
                {"job_id": job_id},
            ).fetchone()
        if not row:
            return None
        return row[0]

    def get_latest_completed_job_id(self, repo_url: str) -> str | None:
        with self._get_connection() as connection:
            row = connection.execute(
                text(
                    """
                SELECT job_id
                FROM analysis_jobs
                WHERE repo_url = :repo_url AND status = 'completed'
                ORDER BY updated_at DESC
                LIMIT 1
                """
                ),
                {"repo_url": repo_url},
            ).fetchone()
        return row[0] if row else None

    def get_latest_completed_result(self, repo_url: str) -> dict[str, Any] | None:
        """Return stored analysis JSON for the most recent completed job for this repo URL."""
        with self._get_connection() as connection:
            row = connection.execute(
                text(
                    """
                SELECT result_json
                FROM analysis_jobs
                WHERE repo_url = :repo_url AND status = 'completed' AND result_json IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT 1
                """
                ),
                {"repo_url": repo_url},
            ).fetchone()
        if not row or not row[0]:
            return None
        return json.loads(row[0])

    def replace_chunks_for_job(self, job_id: str, chunks: list[dict[str, Any]]) -> None:
        with self._get_connection() as connection:
            connection.execute(
                text("DELETE FROM analysis_chunks WHERE job_id = :job_id"),
                {"job_id": job_id},
            )
            connection.execute(
                text(
                    """
                INSERT INTO analysis_chunks (job_id, file_path, chunk_index, content, start_line, end_line)
                VALUES (:job_id, :file_path, :chunk_index, :content, :start_line, :end_line)
                """
                ),
                [
                    {
                        "job_id": job_id,
                        "file_path": chunk["file_path"],
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"],
                        "start_line": chunk.get("start_line"),
                        "end_line": chunk.get("end_line"),
                    }
                    for chunk in chunks
                ],
            )
            connection.commit()

    def get_chunks_for_repo(self, repo_url: str, limit: int = 200) -> list[dict[str, Any]]:
        with self._get_connection() as connection:
            latest_job = connection.execute(
                text(
                    """
                SELECT job_id
                FROM analysis_jobs
                WHERE repo_url = :repo_url AND status = 'completed'
                ORDER BY updated_at DESC
                LIMIT 1
                """
                ),
                {"repo_url": repo_url},
            ).fetchone()
            if not latest_job:
                return []
            rows = connection.execute(
                text(
                    """
                SELECT file_path, chunk_index, content, start_line, end_line
                FROM analysis_chunks
                WHERE job_id = :job_id
                ORDER BY chunk_index ASC
                LIMIT :limit
                """
                ),
                {"job_id": latest_job[0], "limit": limit},
            ).fetchall()

        return [
            {
                "file_path": row[0],
                "chunk_index": row[1],
                "content": row[2],
                "start_line": row[3],
                "end_line": row[4],
            }
            for row in rows
        ]
