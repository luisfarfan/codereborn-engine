"""
Project Understanding router — Domain 2.
Stub: full implementation added when StackDetector / ContextBuilder agents are ready.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/understanding", tags=["Understanding"])


@router.get("/{job_id}/stack", summary="[stub] Get stack intelligence report")
async def get_stack(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "understanding", "job_id": job_id}


@router.get("/{job_id}/context", summary="[stub] Get architecture context")
async def get_context(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "understanding", "job_id": job_id}
