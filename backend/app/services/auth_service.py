"""
Auth Service — Phase 2.
Handles:
  - JWT token creation and verification
  - GitHub OAuth token exchange and user-info fetch
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from jose import JWTError, jwt

from app.core.config import get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo
        self._settings = get_settings()

    # ── JWT helpers ──────────────────────────────────────────────

    def create_access_token(self, user_id: str) -> str:
        """Create a signed JWT containing the user_id as subject."""
        expire = datetime.now(tz=timezone.utc) + timedelta(
            minutes=self._settings.jwt_expire_minutes
        )
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(
            payload,
            self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> Optional[str]:
        """Return user_id from a valid JWT, or None if invalid/expired."""
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret,
                algorithms=[self._settings.jwt_algorithm],
            )
            return payload.get("sub")
        except JWTError:
            return None

    # ── GitHub OAuth ─────────────────────────────────────────────

    def get_github_authorize_url(self, state: str) -> str:
        """Build the GitHub OAuth authorization redirect URL."""
        return (
            f"{GITHUB_AUTHORIZE_URL}"
            f"?client_id={self._settings.github_client_id}"
            f"&scope=read:user,user:email"
            f"&state={state}"
        )

    async def exchange_github_code(self, code: str) -> User:
        """Exchange a GitHub OAuth code for a user record."""
        async with httpx.AsyncClient() as client:
            # Step 1: get access token
            token_resp = await client.post(
                GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self._settings.github_client_id,
                    "client_secret": self._settings.github_client_secret,
                    "code": code,
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise ValueError("GitHub did not return an access token")

            auth_headers = {"Authorization": f"Bearer {access_token}"}

            # Step 2: get user profile
            user_resp = await client.get(GITHUB_USER_URL, headers=auth_headers)
            user_resp.raise_for_status()
            github_user = user_resp.json()

            # Step 3: get primary email if not public
            email: Optional[str] = github_user.get("email")
            if not email:
                emails_resp = await client.get(GITHUB_EMAILS_URL, headers=auth_headers)
                if emails_resp.status_code == 200:
                    for entry in emails_resp.json():
                        if entry.get("primary") and entry.get("verified"):
                            email = entry["email"]
                            break

        return self._user_repo.upsert_github_user(
            github_id=github_user["id"],
            login=github_user["login"],
            name=github_user.get("name"),
            email=email,
            avatar_url=github_user.get("avatar_url"),
        )
