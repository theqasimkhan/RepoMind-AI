"""
User Repository — Phase 2.
SQLite-backed CRUD for users.
"""
import uuid
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from app.models.user import User


class UserRepository:
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
        with self._get_connection() as conn:
            conn.execute(
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
            conn.commit()

    def upsert_github_user(
        self,
        github_id: int,
        login: str,
        name: str | None,
        email: str | None,
        avatar_url: str | None,
    ) -> User:
        """Create or update a user from GitHub OAuth data. Returns the User."""
        with self._get_connection() as conn:
            # Try to find existing user
            row = conn.execute(
                text("SELECT id FROM users WHERE github_id = :github_id"), 
                {"github_id": github_id}
            ).fetchone()

            if row:
                user_id = row[0]
                conn.execute(
                    text("""
                    UPDATE users
                    SET login = :login, name = :name, email = :email, avatar_url = :avatar_url,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE github_id = :github_id
                    """),
                    {
                        "login": login,
                        "name": name,
                        "email": email,
                        "avatar_url": avatar_url,
                        "github_id": github_id,
                    },
                )
            else:
                user_id = str(uuid.uuid4())
                conn.execute(
                    text("""
                    INSERT INTO users (id, github_id, login, name, email, avatar_url)
                    VALUES (:id, :github_id, :login, :name, :email, :avatar_url)
                    """),
                    {
                        "id": user_id,
                        "github_id": github_id,
                        "login": login,
                        "name": name,
                        "email": email,
                        "avatar_url": avatar_url,
                    },
                )
            conn.commit()

        return self.get_by_id(user_id)  # type: ignore[return-value]

    def get_by_id(self, user_id: str) -> User | None:
        with self._get_connection() as conn:
            row = conn.execute(
                text("""
                SELECT id, github_id, login, name, email, avatar_url, created_at, updated_at
                FROM users WHERE id = :id
                """),
                {"id": user_id},
            ).fetchone()
        if not row:
            return None
        return _row_to_user(row)

    def get_by_github_id(self, github_id: int) -> User | None:
        with self._get_connection() as conn:
            row = conn.execute(
                text("""
                SELECT id, github_id, login, name, email, avatar_url, created_at, updated_at
                FROM users WHERE github_id = :github_id
                """),
                {"github_id": github_id},
            ).fetchone()
        if not row:
            return None
        return _row_to_user(row)


def _row_to_user(row: Any) -> User:
    return User(
        id=row[0],
        github_id=row[1],
        login=row[2],
        name=row[3],
        email=row[4],
        avatar_url=row[5],
        created_at=row[6],
        updated_at=row[7],
    )
