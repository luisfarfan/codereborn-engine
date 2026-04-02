"""
Codebase Navigation router — Domain 3.
Stub: full implementation added when SystemMapper agent is ready.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/navigation", tags=["Navigation"])


@router.get("/{job_id}/map", summary="[stub] Get system map")
async def get_map(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "navigation", "job_id": job_id}


@router.get("/{job_id}/search", summary="[stub] Search codebase symbols")
async def search(job_id: str, q: str = "") -> dict:
    return {"status": "not_implemented", "domain": "navigation", "job_id": job_id, "query": q}
