"""
Response schemas (Pydantic models) for the API layer.

These are the serialization shapes returned to API consumers.
They are intentionally flat/simple — no SQLModel, no ORM relationships.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, computed_field

from app.domain.enums import AgentStatus, JobStatus


# ── Job Responses ─────────────────────────────────────────────────────────────


class JobSummaryResponse(BaseModel):
    """Flat Job row for GET /jobs list — optimized for table rendering."""

    id: uuid.UUID
    repo_url: str | None
    repo_path: str | None
    branch: str | None
    tier: str | None
    status: JobStatus
    analysis_scope: str | None  # backend/frontend/mobile/etc.
    tokens_used: int
    cost_usd: float
    models_used: list[str]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_detail: str | None

    @computed_field  # type: ignore[misc]
    @property
    def repo_name(self) -> str | None:
        """Derived from repo_url: github.com/org/name → name."""
        if self.repo_url:
            return self.repo_url.rstrip("/").split("/")[-1]
        if self.repo_path:
            return self.repo_path.rstrip("/").split("/")[-1]
        return None

    @computed_field  # type: ignore[misc]
    @property
    def duration_seconds(self) -> int | None:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    model_config = {"from_attributes": True}


class AgentExecutionResponse(BaseModel):
    """Single agent execution row for GET /jobs/{id} agents tab."""

    agent_id: str           # agent_name column in DB
    agent_name: str         # human-readable label
    status: AgentStatus
    model: str | None
    started_at: datetime | None
    completed_at: datetime | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    output_type: str | None
    output_summary: str | None

    @computed_field  # type: ignore[misc]
    @property
    def duration_seconds(self) -> int | None:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    model_config = {"from_attributes": True}


class OutputMetaResponse(BaseModel):
    """Metadata entry for an available output artifact."""

    type: str            # stack_report, system_map, etc.
    agent_id: str
    format: str          # json | markdown
    size_bytes: int | None = None
    url: str             # relative URL to fetch it


class JobDetailResponse(BaseModel):
    """Full Job detail for GET /jobs/{id} — includes agents, outputs, logs ref."""

    # Core job fields
    id: uuid.UUID
    repo_url: str | None
    repo_path: str | None
    branch: str | None
    tier: str | None
    status: JobStatus
    analysis_scope: str | None
    tokens_used: int
    cost_usd: float
    models_used: list[str]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_detail: str | None

    # Sub-resources
    agents: list[AgentExecutionResponse] = []
    outputs: list[OutputMetaResponse] = []
    logs: dict[str, Any] = {}       # { url: str, total_entries: int }

    @computed_field  # type: ignore[misc]
    @property
    def repo_name(self) -> str | None:
        if self.repo_url:
            return self.repo_url.rstrip("/").split("/")[-1]
        if self.repo_path:
            return self.repo_path.rstrip("/").split("/")[-1]
        return None

    @computed_field  # type: ignore[misc]
    @property
    def duration_seconds(self) -> int | None:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    model_config = {"from_attributes": True}


class JobCreateResponse(BaseModel):
    """Response for POST /jobs — minimal, navigates frontend to live view."""

    job_id: uuid.UUID
    status: JobStatus
    created_at: datetime
    started_at: datetime | None
    repo_url: str | None
    branch: str | None


class JobListResponse(BaseModel):
    """Paginated list response for GET /jobs."""

    jobs: list[JobSummaryResponse]
    total: int
    page: int
    page_size: int


# ── Estimate Response ─────────────────────────────────────────────────────────


class AgentEstimateItem(BaseModel):
    agent_id: str
    agent_name: str
    tokens: int
    cost_usd: float
    duration_minutes: float
    model: str | None = None


class JobEstimateResponse(BaseModel):
    """Response for POST /jobs/estimate."""

    estimated_tokens_total: int
    estimated_cost_usd: float
    estimated_duration_minutes: float
    breakdown_by_agent: list[AgentEstimateItem]
    warnings: list[str] = []


# ── Output Response ───────────────────────────────────────────────────────────


class OutputResponse(BaseModel):
    """Response for GET /jobs/{id}/outputs/{output_type}."""

    type: str
    format: str   # json | markdown
    content: Any  # raw JSON dict or markdown string


# ── Log Response ──────────────────────────────────────────────────────────────


class LogEntry(BaseModel):
    timestamp: datetime
    level: str        # info | warning | error
    agent: str        # agent_name or "system"
    message: str


class JobLogsResponse(BaseModel):
    logs: list[LogEntry]
    total: int


# ── Meta ──────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None
