"""GitHub webhook authentication and pull request event routing."""

import hashlib
import hmac
import json

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pydantic import ValidationError

from ..config import settings
from .schemas import GithubPayload

router = APIRouter()


def verify_signature(payload_body: bytes, signature_header: str | None) -> None:
    """Reject requests that do not have a valid GitHub SHA-256 signature."""
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing")
    if not settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured")
    digest = hmac.new(settings.WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(f"sha256={digest}", signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")


async def run_agent_workflow(payload: GithubPayload) -> None:
    """Entry point queued for accepted pull request events."""
    from ..agent.graph import run_review

    await run_review(payload)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str | int]:
    body = await request.body()
    verify_signature(body, x_hub_signature_256)
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = request.headers.get("X-GitHub-Event", "")
    action = data.get("action")
    if event_type == "pull_request" and action in {"opened", "synchronize"}:
        try:
            payload = GithubPayload.model_validate(data)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
        background_tasks.add_task(run_agent_workflow, payload)
        return {"status": "accepted", "action": action, "number": payload.number}
    return {"status": "ignored", "event": event_type}
