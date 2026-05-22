"""Normalize user-supplied GitHub repository references to a canonical HTTPS clone URL."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_GITHUB = "github.com"
# owner/repo — GitHub allows alphanumeric, hyphen, underscore in names (simplified).
_SLUG = re.compile(r"^[\w.-]+/[\w.-]+$")


def github_repo_slug(clone_url: str) -> str:
    """Return ``owner/repo`` from a canonical ``https://github.com/owner/repo`` URL."""
    path = urlparse(clone_url).path.strip("/")
    return path or "unknown-repository"


def normalize_github_repo_url(raw: str) -> str:
    """
    Accepts:
    - ``https://github.com/owner/repo`` or ``http://www.github.com/...``
    - ``owner/repo``
    - ``github.com/owner/repo``
    - ``git@github.com:owner/repo.git``
    """
    s = (raw or "").strip()
    if not s:
        raise ValueError("Repository URL is required")

    if s.startswith("git@"):
        if "github.com:" in s:
            path = s.split("github.com:", 1)[-1].removesuffix(".git").strip("/")
            if _SLUG.match(path):
                return f"https://{_GITHUB}/{path}"
        raise ValueError(f"Unsupported git SSH URL: {raw!r}")

    if _SLUG.match(s) and "://" not in s:
        return f"https://{_GITHUB}/{s}"

    low = s.lower()
    if low.startswith("github.com/"):
        rest = s.split("/", 1)[-1].strip("/")
        if _SLUG.match(rest):
            return f"https://{_GITHUB}/{rest}"

    if "://" in s:
        p = urlparse(s)
        host = (p.netloc or "").lower().removeprefix("www.")
        if host != _GITHUB:
            raise ValueError("Only github.com repositories are currently supported")
        path = p.path.strip("/")
        if not path or not _SLUG.match(path):
            raise ValueError("Invalid GitHub repository path (expected owner/repo)")
        return f"https://{_GITHUB}/{path}"

    raise ValueError(f"Unsupported GitHub repository URL: {raw!r}")
