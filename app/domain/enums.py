"""
Domain enumerations for CodeReborn Engine.

These are the authoritative enum definitions — kept in the domain layer so
they can be imported by models, services, agents, and API schemas without
creating circular dependencies.
"""

from enum import StrEnum


class AnalysisDepth(StrEnum):
    """Controls which pipeline stages are executed for a job."""

    QUICK = "quick"          # stack detection only (~1 min, low cost)
    STANDARD = "standard"    # stack + system map + context (~5 min)
    FULL = "full"            # all agents including debt and docs (~15 min)


class AnalysisScope(StrEnum):
    """The technical frente of the repository. Detected or explicit."""

    ALL = "all"
    FRONTEND = "frontend"
    BACKEND = "backend"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    LIBRARY = "library"
    WORKER = "worker"
    OTHER = "other"


class AnalysisMode(StrEnum):
    """LLM usage strategy for the pipeline."""

    ECONOMY = "economy"        # prefer cheap/fast models, strict budget
    BALANCED = "balanced"      # mix of models, moderate budget
    QUALITY = "quality"        # best available models, relaxed budget


class AnalysisTier(StrEnum):
    """Frontend-facing tier concept. Maps 1:1 to AnalysisMode internally."""

    BUDGET = "budget"          # → AnalysisMode.ECONOMY
    STANDARD = "standard"      # → AnalysisMode.BALANCED  (default)
    PREMIUM = "premium"        # → AnalysisMode.QUALITY

    def to_analysis_mode(self) -> AnalysisMode:
        """Convert tier to internal AnalysisMode."""
        mapping = {
            AnalysisTier.BUDGET: AnalysisMode.ECONOMY,
            AnalysisTier.STANDARD: AnalysisMode.BALANCED,
            AnalysisTier.PREMIUM: AnalysisMode.QUALITY,
        }
        return mapping[self]


class JobStatus(StrEnum):
    """Lifecycle states of an analysis job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(StrEnum):
    """Execution state of a single agent within a job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LLMDecision(StrEnum):
    """Outcome of the LLMBudgetService evaluation for a proposed call."""

    APPROVE = "approve"
    DOWNGRADE = "downgrade"   # approve with a cheaper model
    REJECT = "reject"         # budget would be exceeded


class TechDebtSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TechDebtCategory(StrEnum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    OUTDATED_DEPENDENCY = "outdated_dependency"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


class DocArtifactType(StrEnum):
    README = "readme"
    API_REFERENCE = "api_reference"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    DATA_FLOW = "data_flow"
    ONBOARDING_GUIDE = "onboarding_guide"
    MIGRATION_GUIDE = "migration_guide"
    ADR = "adr"               # Architecture Decision Record


class AgentName(StrEnum):
    """Full list of agents in the CodeReborn pipeline."""

    STACK_DETECTOR = "stack_detector"
    PATTERN_DETECTOR = "pattern_detector"
    SYSTEM_MAPPER = "system_mapper"
    DEBT_ANALYZER = "tech_debt_analyzer"
    TECHNICAL_WRITER = "technical_doc_writer"
    HUMAN_WRITER = "human_doc_writer"
    AI_CONTEXT_WRITER = "ai_context_writer"
    DEBT_WRITER = "debt_doc_writer"
