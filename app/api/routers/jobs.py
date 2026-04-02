"""
Job Management router — Domain 1 of the Repo Intelligence Interface.

Endpoints:
  POST   /jobs              Create and queue a new analysis job
  GET    /jobs              List jobs with pagination
  GET    /jobs/{id}         Get job details
  DELETE /jobs/{id}         Cancel a running job
  GET    /jobs/{id}/status  Lightweight status poll (SSE-ready)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_db
from app.api.schemas.requests import CancelJobRequest, CreateJobRequest
from app.api.schemas.responses import JobListResponse, JobResponse
from app.core.exceptions import JobNotFoundError
from app.domain.enums import JobStatus
from app.models.db_models import Job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new analysis job",
)
async def create_job(
    body: CreateJobRequest,
    db: AsyncSession = Depends(get_db),
) -> Job:
    job = Job(
        repo_url=body.repo_url,
        repo_path=body.repo_path,
        analysis_scope=body.analysis_scope.value,
        analysis_mode=body.budget.mode.value,
        status=JobStatus.PENDING.value,
        budget_config={
            "max_usd": body.budget.max_usd,
            "mode": body.budget.mode.value,
        },
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


@router.get(
    "",
    response_model=JobListResponse,
    summary="List analysis jobs",
)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    offset = (page - 1) * page_size
    query = select(Job).order_by(Job.created_at.desc()).offset(offset).limit(page_size)

    if status_filter:
        query = query.where(Job.status == status_filter.value)

    result = await db.execute(query)
    jobs = result.scalars().all()

    count_query = select(Job)
    if status_filter:
        count_query = count_query.where(Job.status == status_filter.value)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return JobListResponse(
        items=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Job:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )
    return job


@router.get(
    "/{job_id}/status",
    summary="Poll job status (lightweight)",
)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return {
        "id": str(job.id),
        "status": job.status,
        "tokens_used": job.tokens_used,
        "cost_usd": job.cost_usd,
        "completed_at": job.completed_at,
    }


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a running job",
)
async def cancel_job(
    job_id: uuid.UUID,
    body: CancelJobRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> None:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if job.status in (JobStatus.COMPLETED.value, JobStatus.CANCELLED.value):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel a job with status '{job.status}'",
        )

    job.status = JobStatus.CANCELLED.value
    if body and body.reason:
        job.error_detail = f"Cancelled: {body.reason}"
    db.add(job)
