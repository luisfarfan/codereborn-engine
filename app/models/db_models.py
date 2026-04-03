"""
SQLModel database models for CodeReborn Engine.

All tables are defined here and registered with SQLModel's metadata so that
Alembic can generate migrations from a single source of truth.

Relationships are expressed via FK columns only (no ORM back-populates) to
keep the model layer thin and avoid circular loading issues with async sessions.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Index, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlmodel import Field, SQLModel


def _uuid_pk() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.utcnow()


# ── Job ──────────────────────────────────────────────────────────────────────


class Job(SQLModel, table=True):
    """
    Top-level record for a single analysis run against one repository.
    All agent executions and reports are child records of a Job.
    """

    __tablename__ = "jobs"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    repo_url: str | None = Field(default=None, index=True)
    repo_path: str | None = Field(default=None)

    analysis_depth: str = Field(default="standard", index=True)
    analysis_mode: str = Field(default="balanced")
    status: str = Field(default="pending", index=True)

    budget_config: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    tokens_used: int = Field(default=0)
    cost_usd: float = Field(default=0.0)

    created_at: datetime = Field(default_factory=_now)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_detail: str | None = Field(default=None)


# ── AgentExecution ───────────────────────────────────────────────────────────


class AgentExecution(SQLModel, table=True):
    """
    Tracks the execution of a single CrewAI agent task within a Job.
    One row per agent per job.
    """

    __tablename__ = "agent_executions"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    )
    agent_name: str = Field(index=True)
    status: str = Field(default="pending")  # AgentStatus enum value

    tokens_used: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    llm_calls: int = Field(default=0)

    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_detail: str | None = Field(default=None)

    __table_args__ = (
        Index("ix_agent_executions_job_agent", "job_id", "agent_name"),
    )


# ── StackReport ──────────────────────────────────────────────────────────────


class StackReport(SQLModel, table=True):
    """
    Output of the StackDetector agent.
    Stores the detected languages, frameworks, and tooling of the repository.
    Strictly follows StackIntelligenceReport contract from ai_spec/05_data_contracts.json.
    """

    __tablename__ = "stack_reports"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, unique=True, index=True)
    )

    analysis_scope: str = Field(index=True)  # AnalysisScope enum value
    primary_language: str | None = Field(default=None, index=True)
    confidence_score: float = Field(default=0.0)

    # Full structured data as defined in ai_spec/05_data_contracts.json
    # Contains: stack_summary, languages, frameworks, dependencies, services, hints, etc.
    report_data: dict[str, Any] = Field(
        default={}, sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    )

    # Optional: Backup of the raw output from the underlying tool (specfy)
    raw_tool_output: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )

    created_at: datetime = Field(default_factory=_now)
    analysis_timestamp: datetime = Field(default_factory=_now)


# ── ArchitectureContext ───────────────────────────────────────────────────────


class ArchitectureContext(SQLModel, table=True):
    """
    Output of the ContextBuilder agent.
    Provides a structured description of architectural patterns found.
    """

    __tablename__ = "architecture_contexts"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    )

    architectural_pattern: str | None = Field(default=None)
    entry_points: list[Any] = Field(
        default=[],
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    )
    key_modules: list[Any] = Field(
        default=[],
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    )
    dependency_graph: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    complexity_score: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=_now)


# ── SystemMap ─────────────────────────────────────────────────────────────────


class SystemMap(SQLModel, table=True):
    """
    Output of the SystemMapper agent.
    A navigable map of the codebase: files, classes, functions, relationships.
    """

    __tablename__ = "system_maps"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    )

    total_files: int = Field(default=0)
    total_lines: int = Field(default=0)
    file_tree: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    public_interfaces: list[Any] = Field(
        default=[],
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    )
    created_at: datetime = Field(default_factory=_now)


# ── TechDebtFinding ───────────────────────────────────────────────────────────


class TechDebtFinding(SQLModel, table=True):
    """
    A single tech-debt issue found by the DebtAnalyzer agent.
    Multiple findings per job.
    """

    __tablename__ = "tech_debt_findings"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    )

    category: str = Field(index=True)       # TechDebtCategory
    severity: str = Field(index=True)       # TechDebtSeverity
    title: str
    description: str
    file_path: str | None = Field(default=None)
    line_number: int | None = Field(default=None)
    effort_days: float | None = Field(default=None)
    suggested_fix: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_now)


# ── DocArtifact ───────────────────────────────────────────────────────────────


class DocArtifact(SQLModel, table=True):
    """
    A generated documentation file produced by the DocWriters agent crew.
    """

    __tablename__ = "doc_artifacts"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    )

    artifact_type: str = Field(index=True)  # DocArtifactType
    title: str
    content_md: str
    output_path: str | None = Field(default=None)
    word_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=_now)


# ── LLMCallDecision ───────────────────────────────────────────────────────────


class LLMCallDecision(SQLModel, table=True):
    """
    Audit log of every LLM call evaluation made by LLMBudgetService.
    Enables cost analysis and debugging of budget decisions.
    """

    __tablename__ = "llm_call_decisions"

    id: uuid.UUID = Field(
        default_factory=_uuid_pk,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid_pk),
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    )
    agent_name: str
    requested_model: str
    approved_model: str | None = Field(default=None)
    decision: str      # LLMDecision enum value
    estimated_cost_usd: float
    budget_remaining_usd: float
    reason: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_now)
