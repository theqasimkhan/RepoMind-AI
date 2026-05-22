"""
Auth API Router — Phase 2.
Endpoints:
  GET  /api/v1/auth/github          → redirect to GitHub OAuth
  GET  /api/v1/auth/github/callback  → handle OAuth callback, set JWT cookie, redirect to frontend
  GET  /api/v1/auth/me               → return current authenticated user
  POST /api/v1/auth/logout           → clear auth cookie
"""
import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service() -> AuthService:
    settings = get_settings()
    return AuthService(UserRepository(settings.sqlite_db_path))


@router.get("/github")
async def github_login() -> RedirectResponse:
    """Redirect the browser to GitHub to begin OAuth flow."""
    svc = _get_auth_service()
    state = secrets.token_urlsafe(16)
    url = svc.get_github_authorize_url(state=state)
    response = RedirectResponse(url=url)
    # Store state in a short-lived cookie for CSRF check (optional enhancement)
    response.set_cookie("oauth_state", state, max_age=300, httponly=True, samesite="lax")
    return response


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(default=""),
) -> RedirectResponse:
    """GitHub redirects here with a one-time code. Exchange it for a JWT."""
    svc = _get_auth_service()
    settings = get_settings()

    # Validate OAuth state to prevent CSRF
    oauth_state = request.cookies.get("oauth_state")
    if not oauth_state or oauth_state != state:
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=invalid_state"
        )

    try:
        user = await svc.exchange_github_code(code)
        token = svc.create_access_token(user.id)
    except (ValueError, httpx.HTTPError) as exc:
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={str(exc)[:120]}"
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(f"Unexpected error in OAuth callback: {exc}", exc_info=True)
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=server_error"
        )

    # Use only httpOnly cookie for token transmission (more secure than URL param)
    response = RedirectResponse(url=f"{settings.frontend_url}/auth/callback")
    response.set_cookie(
        "repomind_token",
        token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
    )
    response.delete_cookie("oauth_state")
    return response


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Return the currently authenticated user's profile."""
    return {
        "id": current_user.id,
        "login": current_user.login,
        "name": current_user.name,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at,
    }


@router.post("/logout")
async def logout(response: Response) -> dict:
    """Clear the auth cookie."""
    response.delete_cookie("repomind_token")
    return {"success": True}
