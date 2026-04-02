"""
Response schemas (Pydantic models) for the API layer.

These are the serialization shapes returned to API consumers.
They are intentionally flat/simple — no SQLModel, no ORM relationships.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import JobStatus, AnalysisScope, AnalysisMode


class JobResponse(BaseModel):
    """Serialized Job returned by GET /jobs/{id} and POST /jobs."""

    id: uuid.UUID
    repo_url: str | None
    repo_path: str | None
    analysis_scope: AnalysisScope
    analysis_mode: AnalysisMode
    status: JobStatus
    tokens_used: int
    cost_usd: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_detail: str | None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int


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
