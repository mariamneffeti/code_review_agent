"""FastAPI application for GitHub pull request review webhooks."""

from fastapi import FastAPI

from .webhook import router as webhook_router

app = FastAPI(title="Code Review Agent", version="0.1.0")
app.include_router(webhook_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
