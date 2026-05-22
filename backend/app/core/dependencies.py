"""
FastAPI dependencies — Phase 2.
Provides get_current_user and get_optional_user for route injection.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)

JWT_COOKIE_NAME = "repomind_token"


def _jwt_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    if credentials and credentials.credentials:
        return credentials.credentials.strip() or None
    raw = request.cookies.get(JWT_COOKIE_NAME)
    return raw.strip() if raw else None


def _make_auth_service() -> AuthService:
    settings = get_settings()
    return AuthService(UserRepository(settings.sqlite_db_path))


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> User:
    """Require a valid JWT from Bearer header or repomind_token cookie. Raises 401 if missing or invalid."""
    token = _jwt_from_request(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    svc = _make_auth_service()
    user_id = svc.decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    user = UserRepository(settings.sqlite_db_path).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[User]:
    """Return the authenticated user or None (for public endpoints with optional auth)."""
    token = _jwt_from_request(request, credentials)
    if not token:
        return None
    svc = _make_auth_service()
    user_id = svc.decode_access_token(token)
    if not user_id:
        return None
    settings = get_settings()
    return UserRepository(settings.sqlite_db_path).get_by_id(user_id)
