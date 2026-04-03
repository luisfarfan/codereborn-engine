"""
Pydantic models for StackDetector outputs.

These models strictly follow the contracts defined in
docs/ai_spec/05_data_contracts.json and 03_pipeline_agents.json.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import AnalysisScope


class LanguageInfo(BaseModel):
    language: str
    estimated_percentage: float = Field(ge=0.0, le=100.0)


class FrameworkInfo(BaseModel):
    name: str
    version: str | None = None
    category: str  # e.g. 'web_framework', 'state_management'
    confidence_score: float = Field(ge=0.0, le=1.0)


class DependencyInfo(BaseModel):
    name: str
    version: str | None = None
    dep_type: str  # runtime, dev, peer


class ServiceInfo(BaseModel):
    name: str
    service_type: str  # database, cache, queue, external_api
    description: str | None = None


class InfraHint(BaseModel):
    signal: str
    description: str | None = None


class DockerHints(BaseModel):
    dockerfile_present: bool
    compose_present: bool
    services_defined: list[str] = []


class BuildToolInfo(BaseModel):
    name: str
    tool_type: str | None = None


class TestFrameworkInfo(BaseModel):
    name: str
    language: str


class EntrypointInfo(BaseModel):
    file_path: str
    role: str  # main, server, app, index
    description: str | None = None


class ConfigFileInfo(BaseModel):
    file_path: str
    config_type: str  # env, docker, ci, lint, build
    description: str | None = None


class MonorepoSignals(BaseModel):
    is_monorepo: bool
    signals: list[str] = []


class UnknownSignal(BaseModel):
    signal: str
    description: str | None = None


class StackIntelligenceReport(BaseModel):
    """
    Final output structure for the StackDetector agent.
    Zero LLM tokens used - deterministic analysis.
    """
    model_config = ConfigDict(populate_by_name=True)

    stack_summary: str
    project_name: str | None = None
    analysis_scope: AnalysisScope
    primary_language: str
    languages: list[LanguageInfo] = []
    frameworks: list[FrameworkInfo] = []
    dependencies: list[DependencyInfo] = []
    services: list[ServiceInfo] = []
    infra_hints: list[InfraHint] = []
    docker_hints: DockerHints
    build_tools: list[BuildToolInfo] = []
    test_frameworks: list[TestFrameworkInfo] = []
    entrypoints: list[EntrypointInfo] = []
    config_files: list[ConfigFileInfo] = []
    evidence_files: dict[str, list[str]] = {}
    package_managers: list[str] = []
    monorepo_signals: MonorepoSignals
    confidence_score: float = Field(ge=0.0, le=1.0)
    unknowns: list[UnknownSignal] = []
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
