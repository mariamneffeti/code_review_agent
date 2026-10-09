import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from src.config import settings
from src.listener import webhook
from src.listener.app import app


def _payload():
    return {
        "action": "opened",
        "number": 17,
        "repository": {"name": "demo", "full_name": "octo/demo", "owner": {"login": "octo"}},
        "pull_request": {"number": 17, "title": "Add feature", "head": {}, "base": {}},
    }


def _signature(body, secret):
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_health_returns_200():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_rejects_invalid_hmac(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "test-secret")
    body = json.dumps(_payload()).encode()
    response = TestClient(app).post(
        "/webhook", content=body, headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=bad"}
    )
    assert response.status_code == 403


def test_webhook_accepts_valid_signature_and_enqueues(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "test-secret")
    enqueued = []

    async def fake_workflow(payload):
        enqueued.append(payload.number)

    monkeypatch.setattr(webhook, "run_agent_workflow", fake_workflow)
    body = json.dumps(_payload()).encode()
    response = TestClient(app).post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": _signature(body, "test-secret"),
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert enqueued == [17]
