"""GitHub REST API tools used by the pull request review agent."""

from dataclasses import dataclass

import httpx

from ..config import settings

GITHUB_API = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    """Raised when GitHub rejects a request or cannot be reached."""


@dataclass(frozen=True)
class PullRequestRef:
    repository: str
    pull_number: int


@dataclass(frozen=True)
class ReviewComment:
    repository: str
    pull_number: int
    body: str


def _headers() -> dict[str, str]:
    if not settings.GITHUB_TOKEN:
        raise GitHubAPIError("GITHUB_TOKEN is not configured")
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_pr_diff(repository: str, pull_number: int) -> str:
    """Fetch a PR's unified diff from GitHub."""
    ref = PullRequestRef(repository=repository, pull_number=pull_number)
    if ref.pull_number < 1 or "/" not in ref.repository:
        raise ValueError("repository must be owner/name and pull_number must be positive")
    try:
        response = httpx.get(
            f"{GITHUB_API}/repos/{ref.repository}/pulls/{ref.pull_number}",
            headers={**_headers(), "Accept": "application/vnd.github.diff"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as exc:
        raise GitHubAPIError(f"GitHub returned HTTP {exc.response.status_code} while fetching the diff") from exc
    except httpx.RequestError as exc:
        raise GitHubAPIError(f"Could not fetch pull request diff: {exc}") from exc


def post_review_comment(repository: str, pull_number: int, body: str) -> dict[str, object]:
    """Post a general issue comment on a pull request."""
    comment = ReviewComment(repository=repository, pull_number=pull_number, body=body)
    if comment.pull_number < 1 or "/" not in comment.repository:
        raise ValueError("repository must be owner/name and pull_number must be positive")
    if not comment.body.strip():
        raise ValueError("comment body must not be empty")
    try:
        response = httpx.post(
            f"{GITHUB_API}/repos/{comment.repository}/issues/{comment.pull_number}/comments",
            headers=_headers(),
            json={"body": comment.body},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise GitHubAPIError("GitHub returned an invalid comment response")
        return data
    except httpx.HTTPStatusError as exc:
        raise GitHubAPIError(f"GitHub returned HTTP {exc.response.status_code} while posting the comment") from exc
    except httpx.RequestError as exc:
        raise GitHubAPIError(f"Could not post pull request comment: {exc}") from exc
