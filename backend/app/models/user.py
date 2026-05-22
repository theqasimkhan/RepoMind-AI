"""
User model — Phase 2 multi-user support.
Stores GitHub OAuth users. No passwords; all auth flows through GitHub.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: str                    # UUID primary key
    github_id: int             # GitHub numeric user ID (unique)
    login: str                 # GitHub username
    name: Optional[str]        # Display name
    email: Optional[str]       # Primary email (may be None if private)
    avatar_url: Optional[str]  # GitHub avatar
    created_at: str
    updated_at: str
