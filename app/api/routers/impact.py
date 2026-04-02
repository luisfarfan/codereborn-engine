"""
Impact Analysis router — Domain 5.
Stub: full implementation added when DebtAnalyzer agent is ready.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/impact", tags=["Impact"])


@router.get("/{job_id}/debt", summary="[stub] Get tech debt findings")
async def get_debt(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "impact", "job_id": job_id}


@router.get("/{job_id}/debt/summary", summary="[stub] Get tech debt summary")
async def get_debt_summary(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "impact", "job_id": job_id}
