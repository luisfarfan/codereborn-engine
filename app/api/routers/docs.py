"""
Documentation router — Domain 6.
Stub: full implementation added when DocWriters agent crew is ready.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/docs-gen", tags=["Docs"])


@router.post("/{job_id}/generate", summary="[stub] Trigger documentation generation")
async def generate_docs(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "docs", "job_id": job_id}


@router.get("/{job_id}/artifacts", summary="[stub] List generated doc artifacts")
async def list_artifacts(job_id: str) -> dict:
    return {"status": "not_implemented", "domain": "docs", "job_id": job_id}
