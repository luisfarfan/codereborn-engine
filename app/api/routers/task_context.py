"""
Task Context router — Domain 4.
Stub: full implementation added when ContextBuilder agent is ready.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/task-context", tags=["Task Context"])


@router.post("/{job_id}/generate", summary="[stub] Generate AI task context")
async def generate_context(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "task_context", "job_id": job_id}
