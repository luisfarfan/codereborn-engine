"""
Pydantic models for StackDetector outputs.

These models strictly follow the contracts defined in
docs/ai_spec/05_data_contracts.json and 03_pipeline_agents.json.
"""

from datetime import datetime
from typing import Any
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
    evidence: str | None = None
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
    evidence: str | None = None
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


# --- New Models for Universal Signal Extraction ---

class LanguageFileBreakdown(BaseModel):
    code_files: list[str] = []
    test_files: list[str] = []
    total_files: int = 0
    total_lines_of_code: int = 0


class FileInventory(BaseModel):
    by_language: dict[str, LanguageFileBreakdown] = {}
    by_type: dict[str, int] = {
        "code": 0,
        "tests": 0,
        "configs": 0,
        "docs": 0,
        "other": 0
    }
    total_files: int = 0
    excluded_files: int = 0
    exclusion_reasons: dict[str, int] = {
        "vendor_dependencies": 0,
        "generated_code": 0,
        "binary_files": 0,
        "hidden_files": 0
    }


class DirectoryNode(BaseModel):
    path: str
    name: str
    depth: int
    parent: str | None = None
    subdirectories: list[str] = []
    file_count: int = 0
    file_breakdown: dict[str, int] = {}
    total_lines: int = 0


class DirectoryStructure(BaseModel):
    root_directories: list[DirectoryNode] = []
    statistics: dict[str, Any] = {
        "total_directories": 0,
        "max_depth": 0,
        "largest_directory": {"path": "", "file_count": 0}
    }


class RepositoryMetadata(BaseModel):
    total_size_bytes: int = 0
    git_available: bool = False
    branch_analyzed: str | None = None
    last_commit_date: str | None = None
    file_count_by_depth: dict[str, int] = {}


class StackIntelligenceReport(BaseModel):
    """
    Final output structure for the StackDetector agent.
    Zero LLM tokens used - deterministic analysis.
    """
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

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
    
    # NEW fields from spec
    file_inventory: FileInventory = Field(default_factory=FileInventory)
    directory_structure: DirectoryStructure = Field(default_factory=DirectoryStructure)
    repository_metadata: RepositoryMetadata = Field(default_factory=RepositoryMetadata)
    
    confidence_score: float = Field(ge=0.0, le=1.0)
    unknowns: list[UnknownSignal] = []
    agent_version: str = "2.0.0"
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- Pattern Detector Models (V3 Architectura) ---

class DetectedPattern(BaseModel):
    pattern: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = []


class PatternInsight(BaseModel):
    primary_pattern: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = []
    secondary_patterns: list[DetectedPattern] = []
    notes: str | None = None
    confidence_score: float | None = None  # To catch variations in LLM naming


class DirectoryInterpretation(BaseModel):
    purpose: str
    architectural_role: str
    priority: str  # critical, high, medium, low, ignore
    reasoning: str | None = None


class FrameworkConvention(BaseModel):
    convention: str
    detected_in: str
    confidence: float = Field(ge=0.0, le=1.0)
    implication: str | None = None


class SamplingRule(BaseModel):
    strategy: str  # analyze_all, sample, skip
    file_count: int | None = None
    sample_size: int | None = None
    sample_method: str | None = None  # largest_files_first, diverse_selection, etc.
    reason: str | None = None


class SamplingStrategy(BaseModel):
    total_files_in_repo: int
    recommended_sample_size: int
    sampling_rules: dict[str, SamplingRule] = {}
    recommended_files: list[dict[str, Any]] = []


class SpecialCase(BaseModel) :
    case: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = []
    impact: str | None = None


class AnalysisMetadata(BaseModel):
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_version: str = "1.0.0"
    llm_model_used: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0


class PatternReport(BaseModel):
    """
    Output structure for the Pattern Detector agent.
    Interprets structure into architectural patterns.
    """
    detected_patterns: PatternInsight
    directory_interpretation: dict[str, DirectoryInterpretation] = {}
    framework_conventions: list[FrameworkConvention] = []
    sampling_strategy: SamplingStrategy
    special_cases: list[SpecialCase] = []
    
    # Metadata nested as per PROMPTS/pattern_detector.md
    analysis_metadata: AnalysisMetadata = Field(default_factory=AnalysisMetadata)
    
    # Root level confidence for safety
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
