import pytest

from app.utils.repo_url import github_repo_slug, normalize_github_repo_url


def test_normalize_https() -> None:
    u = normalize_github_repo_url("https://github.com/foo/bar")
    assert u == "https://github.com/foo/bar"


def test_normalize_owner_repo_slug() -> None:
    u = normalize_github_repo_url("theqasimkhan/MultiModal-AI-for-Chest-Xrays")
    assert u == "https://github.com/theqasimkhan/MultiModal-AI-for-Chest-Xrays"


def test_normalize_github_com_prefix() -> None:
    u = normalize_github_repo_url("github.com/foo/bar")
    assert u == "https://github.com/foo/bar"


def test_normalize_git_ssh() -> None:
    u = normalize_github_repo_url("git@github.com:foo/bar.git")
    assert u == "https://github.com/foo/bar"


def test_github_repo_slug() -> None:
    assert github_repo_slug("https://github.com/o/r") == "o/r"


def test_reject_non_github_host() -> None:
    with pytest.raises(ValueError):
        normalize_github_repo_url("https://gitlab.com/foo/bar")
