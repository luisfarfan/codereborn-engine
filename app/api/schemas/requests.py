"""
Request schemas (Pydantic models) for the API layer.

These are the validated input shapes for all POST/PATCH endpoints.
They are separate from the DB models — no SQLModel table flag here.
"""

from pydantic import BaseModel, field_validator

from app.domain.enums import AnalysisTier


class AgentConfigItem(BaseModel):
    """Per-agent configuration override within a Job request."""

    agent_id: str
    enabled: bool = True
    model: str | None = None  # None = use tier default


class CreateJobRequest(BaseModel):
    """Body for POST /api/v1/jobs — start a new analysis job."""

    # Source — at least one must be provided
    repo_url: str | None = None
    repo_path: str | None = None  # kept for CLI compatibility

    branch: str = "main"
    github_token: str | None = None  # stored as ref only, never returned

    # Analysis configuration
    tier: AnalysisTier = AnalysisTier.STANDARD
    agent_configs: list[AgentConfigItem] = []

    @field_validator("repo_url", "repo_path", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    def model_post_init(self, __context: object) -> None:
        if not self.repo_url and not self.repo_path:
            raise ValueError("Provide either repo_url or repo_path")


class EstimateJobRequest(CreateJobRequest):
    """Body for POST /api/v1/jobs/estimate — same shape as CreateJobRequest."""
    pass


class CancelJobRequest(BaseModel):
    reason: str | None = None
