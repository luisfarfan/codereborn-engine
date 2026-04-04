"""
Notification Service — Internal Redis PubSub publisher.

This service abstracts the communication with the frontend via SSE.
Agents should use this to report progress, state changes, or outputs.

Communication Flow:
  Agent → NotificationService → Redis PubSub (job:{id}:events) → SSE Endpoint → Frontend
"""

import json
import uuid
from datetime import datetime

from app.infrastructure.redis_client import get_redis_client


class NotificationService:
    """
    Singleton-like service to publish events to the frontend via Redis.
    Matches the schema expected by app/api/routers/stream.py and PROMPT_FRONTEND.AI.
    """

    @staticmethod
    async def _publish(job_id: uuid.UUID, event_type: str, data: dict) -> None:
        """Publish a generic event to the job's Redis channel."""
        redis = await get_redis_client()
        channel = f"job:{job_id}:events"
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await redis.publish(channel, json.dumps(payload))

    @classmethod
    async def notify_job_status(cls, job_id: uuid.UUID, status: str) -> None:
        """Inform the frontend of a job-level status change (running, completed, etc)."""
        await cls._publish(job_id, "job_status", {"status": status})

    @classmethod
    async def notify_agent_started(cls, job_id: uuid.UUID, agent_id: str, agent_name: str) -> None:
        """Inform that an agent has started its task."""
        await cls._publish(job_id, "agent_started", {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "started_at": datetime.utcnow().isoformat(),
        })

    @classmethod
    async def notify_agent_progress(
        cls, job_id: uuid.UUID, agent_id: str, percentage: int, message: str
    ) -> None:
        """Send a progress update for a specific agent."""
        await cls._publish(job_id, "agent_progress", {
            "agent_id": agent_id,
            "percentage": percentage,
            "message": message,
        })

    @classmethod
    async def notify_agent_completed(
        cls, job_id: uuid.UUID, agent_id: str, status: str, summary: str | None = None
    ) -> None:
        """Inform that an agent execution has finished."""
        await cls._publish(job_id, "agent_completed", {
            "agent_id": agent_id,
            "status": status,
            "completed_at": datetime.utcnow().isoformat(),
            "output_summary": summary,
        })

    @classmethod
    async def notify_job_completed(cls, job_id: uuid.UUID, cost: float) -> None:
        """Final event when the whole job pipeline is successful."""
        await cls._publish(job_id, "job_completed", {
            "job_id": str(job_id),
            "completed_at": datetime.utcnow().isoformat(),
            "cost_usd": cost,
        })

    @classmethod
    async def notify_job_failed(cls, job_id: uuid.UUID, error: str) -> None:
        """Final event when the job pipeline fails."""
        await cls._publish(job_id, "job_failed", {
            "job_id": str(job_id),
            "error": error,
            "failed_at": datetime.utcnow().isoformat(),
        })
