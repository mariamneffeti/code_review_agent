import hmac
import hashlib
import json
from fastapi import Request, HTTPException, Header,APIRouter,BackgroundTasks
from ..config import settings
from ..listener.schemas import GithubPayload

router = APIRouter()


def verify_signature(payload_body : bytes, signature_header : str):
    """Verify wether the request is from github : webhook secret matches the github signature """
    if not signature_header:
        raise HTTPException(status_code=403,detail="x-hub-signature-256 header is missing")
    hash_object = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.get_secret_value().encode(),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403,detail="Invalid signature")
async def run_agent_workflow(payload: GithubPayload):
    """Run the agent workflow in background"""
    # TODO: Implement the logic to trigger the agent workflow based on the payload
    print(f"Running agent workflow with payload: {payload}")
    pass

@router.post("/webhook")
async def github_webhook(request : Request, background_tasks : BackgroundTasks, x_hub_signature_256 : str = Header(None)):
    payload_body = await request.body()
    verify_signature(payload_body, x_hub_signature_256)
    try:
        data = json.loads(payload_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    event_type = request.headers.get("X-GitHub-Event")
    if event_type == "pull_request":
        action = data.get("action")
        if action in ["opened", "synchronize"]:
            payload = GithubPayload(**data)
            background_tasks.add_task(run_agent_workflow, payload)
            return {"status" : "accepted", "action" : action}
    return {"status" : "ignored", "event" : event_type}
