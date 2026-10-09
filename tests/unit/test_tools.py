import httpx

from src.config import settings
from src.tools import github_api


def test_fetch_pr_diff_with_mocked_httpx(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "test-token")
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, text="diff --git a/file.py b/file.py\n", request=httpx.Request("GET", url))

    monkeypatch.setattr(github_api.httpx, "get", fake_get)
    assert "diff --git" in github_api.fetch_pr_diff("octo/demo", 17)
    assert calls[0][0].endswith("/repos/octo/demo/pulls/17")
    assert calls[0][1]["headers"]["Authorization"] == "Bearer test-token"


def test_post_review_comment_with_mocked_httpx(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "test-token")
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(201, json={"id": 8, "body": kwargs["json"]["body"]}, request=httpx.Request("POST", url))

    monkeypatch.setattr(github_api.httpx, "post", fake_post)
    result = github_api.post_review_comment("octo/demo", 17, "Please handle this edge case.")
    assert result["id"] == 8
    assert calls[0][1]["json"]["body"].startswith("Please handle")
