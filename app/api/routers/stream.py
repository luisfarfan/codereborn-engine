"""
Real-time SSE streaming router — GET /jobs/{job_id}/stream.

Architecture:
  - Agents publish events to Redis PubSub channel: "job:{job_id}:events"
  - This endpoint subscribes to that channel and forwards events to the client
    as Server-Sent Events (SSE).
  - Connection closes automatically when job completes or fails.

This pattern keeps Redis ONLY for PubSub (not for pipeline data),
in full compliance with the architecture rules.

Event types (mirrors PROMPT_FRONTEND.AI spec):
  - job_status
  - agent_started
  - agent_progress
  - agent_output_chunk
  - agent_completed
  - agent_communication
  - job_completed
  - job_failed
"""

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import get_db
from app.infrastructure.redis_client import get_redis_client
from app.models.db_models import Job

router = APIRouter(prefix="/jobs", tags=["Stream"])

# Events that indicate the job has reached a terminal state
_TERMINAL_EVENTS = {"job_completed", "job_failed"}


async def _event_generator(
    job_id: uuid.UUID,
    job_status: str,
) -> AsyncGenerator[dict, None]:
    """
    Subscribe to the Redis PubSub channel for this job and yield SSE events.

    If the job is already completed/failed when the client connects,
    yield a synthetic terminal event immediately and close.
    """
    redis = await get_redis_client()

    # Fast-path: job already done when client connects
    if job_status in ("completed", "failed", "cancelled"):
        yield {
            "event": f"job_{job_status}",
            "data": json.dumps({"status": job_status}),
        }
        return

    channel = f"job:{job_id}:events"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    try:
        # Send initial keepalive so the connection is established quickly
        yield {"event": "ping", "data": json.dumps({"status": "connected", "job_id": str(job_id)})}

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                payload: dict = json.loads(message["data"])
            except (json.JSONDecodeError, TypeError):
                continue

            event_type = payload.get("event", "update")
            yield {
                "event": event_type,
                "data": json.dumps(payload.get("data", payload)),
            }

            # Close the stream when job reaches terminal state
            if event_type in _TERMINAL_EVENTS:
                break
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


@router.get(
    "/{job_id}/stream",
    summary="Real-time SSE stream for a running job",
    description=(
        "Server-Sent Events endpoint. Connect and receive real-time updates "
        "as agents execute. Stream closes automatically when the job completes "
        "or fails. Events mirror the PROMPT_FRONTEND.AI spec."
    ),
    response_class=EventSourceResponse,
)
async def stream_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return EventSourceResponse(
        _event_generator(job_id, job.status),
        ping=15,           # keepalive ping every 15s
        ping_message_factory=lambda: "ping",
    )
