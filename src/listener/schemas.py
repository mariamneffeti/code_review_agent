"""Typed subset of GitHub pull request webhook payloads."""

from pydantic import BaseModel, ConfigDict, Field


class Repository(BaseModel):
    model_config = ConfigDict(extra="allow")
    full_name: str
    name: str
    owner: dict[str, object]


class PullRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    number: int
    title: str = ""
    html_url: str = ""
    diff_url: str = ""
    head: dict[str, object] = Field(default_factory=dict)
    base: dict[str, object] = Field(default_factory=dict)


class GithubPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    action: str
    number: int
    repository: Repository
    pull_request: PullRequest
