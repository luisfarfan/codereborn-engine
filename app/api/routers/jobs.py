"""
Job Management router — full frontend-ready API.

Endpoints:
  POST   /jobs                          Create and queue a new analysis job
  POST   /jobs/estimate                 Estimate cost/duration (no side-effects)
  GET    /jobs                          List jobs with filters + pagination
  GET    /jobs/{id}                     Full job detail (agents, outputs, logs ref)
  DELETE /jobs/{id}                     Cancel a running job
  GET    /jobs/{id}/outputs/{type}      Fetch a specific output artifact
  GET    /jobs/{id}/logs                Fetch execution log timeline
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_db
from app.api.schemas.requests import CancelJobRequest, CreateJobRequest, EstimateJobRequest
from app.api.schemas.responses import (
    AgentExecutionResponse,
    JobCreateResponse,
    JobDetailResponse,
    JobEstimateResponse,
    JobListResponse,
    JobLogsResponse,
    JobSummaryResponse,
    LogEntry,
    OutputMetaResponse,
    OutputResponse,
)
from app.application.job_orchestrator import JobOrchestrator
from app.domain.enums import AgentName, AgentStatus, JobStatus
from app.models.db_models import (
    AgentExecution,
    ArchitectureContext,
    DocArtifact,
    Job,
    StackReport,
    SystemMap,
    TechDebtFinding,
)
from app.services import estimation_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# ── Helpers ───────────────────────────────────────────────────────────────────

_AGENT_DISPLAY_NAMES: dict[str, str] = {
    AgentName.STACK_DETECTOR:  "Stack Detector",
    AgentName.CONTEXT_BUILDER: "Architecture Context Builder",
    AgentName.SYSTEM_MAPPER:   "System Mapper",
    AgentName.DEBT_ANALYZER:   "Tech Debt Analyzer",
    AgentName.TECHNICAL_WRITER: "Technical Doc Writer",
    AgentName.HUMAN_WRITER:    "Human Doc Writer",
    AgentName.AI_CONTEXT_WRITER: "AI Context Writer",
    AgentName.DEBT_WRITER:     "Debt Doc Writer",
}

# Maps output_type string → DB model class for output serving
_OUTPUT_TYPE_MAP = {
    "stack_report":          ("stack_reports",           "report_data"),
    "architecture_context":  ("architecture_contexts",   None),
    "system_map":            ("system_maps",             "file_tree"),
    "tech_debt_analysis":    ("tech_debt_findings",      None),
    "technical_doc":         ("doc_artifacts",           "content_md"),
}


def _build_agent_response(exe: AgentExecution) -> AgentExecutionResponse:
    return AgentExecutionResponse(
        agent_id=exe.agent_name,
        agent_name=_AGENT_DISPLAY_NAMES.get(exe.agent_name, exe.agent_name),
        status=AgentStatus(exe.status),
        model=exe.model_used,
        started_at=exe.started_at,
        completed_at=exe.completed_at,
        input_tokens=exe.input_tokens,
        output_tokens=exe.output_tokens,
        total_tokens=exe.input_tokens + exe.output_tokens,
        cost_usd=exe.cost_usd,
        output_type=exe.output_type,
        output_summary=exe.output_summary,
    )


def _build_output_metas(
    job_id: uuid.UUID, executions: list[AgentExecution]
) -> list[OutputMetaResponse]:
    """Build output metadata list from completed agent executions."""
    outputs = []
    for exe in executions:
        if exe.status != AgentStatus.COMPLETED.value or not exe.output_type:
            continue
        fmt = "markdown" if exe.output_type == "technical_doc" else "json"
        outputs.append(
            OutputMetaResponse(
                type=exe.output_type,
                agent_id=exe.agent_name,
                format=fmt,
                url=f"/api/v1/jobs/{job_id}/outputs/{exe.output_type}",
            )
        )
    return outputs


# ── POST /jobs/estimate — must be BEFORE /{job_id} to avoid routing ambiguity ─


@router.post(
    "/estimate",
    response_model=JobEstimateResponse,
    summary="Estimate cost and duration for a planned job",
    description=(
        "Pure heuristic calculation — no DB writes, no LLM calls. "
        "Call this before POST /jobs to show the user cost confirmation."
    ),
)
async def estimate_job(body: EstimateJobRequest) -> JobEstimateResponse:
    return estimation_service.estimate(body)


# ── POST /jobs ────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start a new analysis job",
)
async def create_job(
    body: CreateJobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    orchestrator: JobOrchestrator = Depends(JobOrchestrator),
) -> JobCreateResponse:
    job = Job(
        repo_url=body.repo_url,
        repo_path=body.repo_path,
        branch=body.branch,
        tier=body.tier.value,
        analysis_mode=body.tier.to_analysis_mode().value,
        status=JobStatus.PENDING.value,
        # NOTE: github_token is intentionally NOT stored in DB.
        # Future: encrypt and store a reference for background workers.
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # Trigger asynchronous execution in the background
    background_tasks.add_task(orchestrator.run_job, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=JobStatus(job.status),
        created_at=job.created_at,
        started_at=job.started_at,
        repo_url=job.repo_url,
        branch=job.branch,
    )


# ── GET /jobs ─────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=JobListResponse,
    summary="List analysis jobs with optional filters",
)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    scope: str | None = Query(default=None, description="Filter by analysis_scope"),
    tier: str | None = Query(default=None, description="Filter by tier"),
    start_date: str | None = Query(default=None, description="ISO date: created after"),
    end_date: str | None = Query(default=None, description="ISO date: created before"),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    offset = (page - 1) * page_size
    query = select(Job).order_by(Job.created_at.desc())

    if status_filter:
        query = query.where(Job.status == status_filter.value)
    if scope:
        query = query.where(Job.analysis_scope == scope)
    if tier:
        query = query.where(Job.tier == tier)
    if start_date:
        query = query.where(Job.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(Job.created_at <= datetime.fromisoformat(end_date))

    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    paged_query = query.offset(offset).limit(page_size)
    result = await db.execute(paged_query)
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[JobSummaryResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /jobs/{job_id} ────────────────────────────────────────────────────────


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Full job detail including agents, outputs, and logs reference",
)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> JobDetailResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    # Fetch agent executions
    exe_result = await db.execute(
        select(AgentExecution)
        .where(AgentExecution.job_id == job_id)
        .order_by(AgentExecution.started_at)
    )
    executions = exe_result.scalars().all()

    agent_responses = [_build_agent_response(exe) for exe in executions]
    output_metas = _build_output_metas(job_id, list(executions))

    return JobDetailResponse(
        id=job.id,
        repo_url=job.repo_url,
        repo_path=job.repo_path,
        branch=job.branch,
        tier=job.tier,
        status=JobStatus(job.status),
        analysis_scope=job.analysis_scope,
        tokens_used=job.tokens_used,
        cost_usd=job.cost_usd,
        models_used=job.models_used or [],
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_detail=job.error_detail,
        agents=agent_responses,
        outputs=output_metas,
        logs={
            "url": f"/api/v1/jobs/{job_id}/logs",
            "total_entries": len(executions) * 3,  # rough estimate
        },
    )


# ── GET /jobs/{job_id}/outputs/{output_type} ──────────────────────────────────


@router.get(
    "/{job_id}/outputs/{output_type}",
    response_model=OutputResponse,
    summary="Fetch a specific output artifact for a completed job",
)
async def get_output(
    job_id: uuid.UUID,
    output_type: str,
    db: AsyncSession = Depends(get_db),
) -> OutputResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if output_type == "stack_report":
        result = await db.execute(select(StackReport).where(StackReport.job_id == job_id))
        report = result.scalars().first()
        if not report:
            raise HTTPException(status_code=404, detail="Stack report not found for this job")
        return OutputResponse(type="stack_report", format="json", content=report.report_data)

    if output_type == "architecture_context":
        result = await db.execute(
            select(ArchitectureContext).where(ArchitectureContext.job_id == job_id)
        )
        ctx = result.scalars().first()
        if not ctx:
            raise HTTPException(status_code=404, detail="Architecture context not found")
        return OutputResponse(
            type="architecture_context",
            format="json",
            content={
                "architectural_pattern": ctx.architectural_pattern,
                "entry_points": ctx.entry_points,
                "key_modules": ctx.key_modules,
                "dependency_graph": ctx.dependency_graph,
                "complexity_score": ctx.complexity_score,
            },
        )

    if output_type == "system_map":
        result = await db.execute(select(SystemMap).where(SystemMap.job_id == job_id))
        smap = result.scalars().first()
        if not smap:
            raise HTTPException(status_code=404, detail="System map not found")
        return OutputResponse(
            type="system_map",
            format="json",
            content={
                "total_files": smap.total_files,
                "total_lines": smap.total_lines,
                "file_tree": smap.file_tree,
                "public_interfaces": smap.public_interfaces,
            },
        )

    if output_type == "tech_debt_analysis":
        result = await db.execute(
            select(TechDebtFinding).where(TechDebtFinding.job_id == job_id)
        )
        findings = result.scalars().all()
        return OutputResponse(
            type="tech_debt_analysis",
            format="json",
            content=[
                {
                    "id": str(f.id),
                    "category": f.category,
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "effort_days": f.effort_days,
                    "suggested_fix": f.suggested_fix,
                }
                for f in findings
            ],
        )

    # DocArtifact types: technical_doc, human_doc, ai_context, debt_doc
    doc_type_map = {
        "technical_doc": "api_reference",
        "human_doc": "onboarding_guide",
        "ai_context": "adr",
        "debt_doc": "data_flow",
    }
    if output_type in doc_type_map:
        result = await db.execute(
            select(DocArtifact)
            .where(DocArtifact.job_id == job_id)
            .where(DocArtifact.artifact_type == doc_type_map[output_type])
        )
        doc = result.scalars().first()
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document '{output_type}' not found")
        return OutputResponse(type=output_type, format="markdown", content=doc.content_md)

    raise HTTPException(
        status_code=400,
        detail=(
            f"Unknown output type '{output_type}'. "
            "Valid: stack_report, architecture_context, system_map, "
            "tech_debt_analysis, technical_doc, human_doc, ai_context, debt_doc"
        ),
    )


# ── GET /jobs/{job_id}/logs ───────────────────────────────────────────────────


@router.get(
    "/{job_id}/logs",
    response_model=JobLogsResponse,
    summary="Get execution log timeline for a job",
)
async def get_logs(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> JobLogsResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    result = await db.execute(
        select(AgentExecution)
        .where(AgentExecution.job_id == job_id)
        .order_by(AgentExecution.started_at)
    )
    executions = result.scalars().all()

    log_entries: list[LogEntry] = []
    created_at = job.created_at

    # Synthetic system events
    log_entries.append(LogEntry(
        timestamp=created_at,
        level="info",
        agent="system",
        message="Job created",
    ))
    if job.started_at:
        log_entries.append(LogEntry(
            timestamp=job.started_at,
            level="info",
            agent="system",
            message="Job started",
        ))

    # Per-agent events
    for exe in executions:
        if exe.started_at:
            log_entries.append(LogEntry(
                timestamp=exe.started_at,
                level="info",
                agent=exe.agent_name,
                message="Agent started",
            ))
        if exe.completed_at:
            if exe.status == AgentStatus.COMPLETED.value:
                msg = "Agent completed successfully"
                if exe.output_summary:
                    msg = exe.output_summary
                log_entries.append(LogEntry(
                    timestamp=exe.completed_at,
                    level="info",
                    agent=exe.agent_name,
                    message=msg,
                ))
            elif exe.status == AgentStatus.FAILED.value:
                log_entries.append(LogEntry(
                    timestamp=exe.completed_at,
                    level="error",
                    agent=exe.agent_name,
                    message=exe.error_detail or "Agent failed",
                ))

    # Final job event
    if job.completed_at:
        final_status = "completed" if job.status == JobStatus.COMPLETED.value else job.status
        log_entries.append(LogEntry(
            timestamp=job.completed_at,
            level="info",
            agent="system",
            message=f"Job {final_status}",
        ))

    log_entries.sort(key=lambda e: e.timestamp)

    return JobLogsResponse(logs=log_entries, total=len(log_entries))


# ── DELETE /jobs/{job_id} ─────────────────────────────────────────────────────


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel a running job",
)
async def cancel_job(
    job_id: uuid.UUID,
    body: CancelJobRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
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

    return {
        "job_id": str(job_id),
        "status": "cancelled",
        "message": "Job stopped successfully",
    }
