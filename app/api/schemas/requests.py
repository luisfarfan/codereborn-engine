"""
Request schemas (Pydantic models) for the API layer.

These are the validated input shapes for all POST/PATCH endpoints.
They are separate from the DB models — no SQLModel table flag here.
"""

from pydantic import BaseModel, HttpUrl, field_validator

from app.domain.enums import AnalysisMode, AnalysisScope


class BudgetConfig(BaseModel):
    max_usd: float = 0.50
    mode: AnalysisMode = AnalysisMode.BALANCED

    @field_validator("max_usd")
    @classmethod
    def validate_budget(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("max_usd must be positive")
        if v > 50.0:
            raise ValueError("max_usd cannot exceed $50 per job")
        return round(v, 4)


class CreateJobRequest(BaseModel):
    """Body for POST /api/v1/jobs — start a new analysis job."""

    repo_url: str | None = None
    repo_path: str | None = None
    analysis_scope: AnalysisScope = AnalysisScope.STANDARD
    budget: BudgetConfig = BudgetConfig()

    @field_validator("repo_url", "repo_path")
    @classmethod
    def at_least_one_source(cls, v: str | None) -> str | None:
        return v

    def model_post_init(self, __context: object) -> None:
        if not self.repo_url and not self.repo_path:
            raise ValueError("Provide either repo_url or repo_path")


class CancelJobRequest(BaseModel):
    reason: str | None = None
