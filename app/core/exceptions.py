"""
Domain-level exception hierarchy for CodeReborn Engine.

Clean Architecture rule: exceptions flow outward — domain raises them,
infrastructure/API layers catch and translate to HTTP responses.
"""


class CodeRebornError(Exception):
    """Base exception for all CodeReborn Engine errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


# ── Job domain ───────────────────────────────────────────────────────────────


class JobNotFoundError(CodeRebornError):
    """Raised when a job ID does not exist."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job '{job_id}' not found")
        self.job_id = job_id


class JobAlreadyRunningError(CodeRebornError):
    """Raised when a duplicate analysis is triggered for the same repo/scope."""

    def __init__(self, repo_url: str) -> None:
        super().__init__(
            f"An analysis job for '{repo_url}' is already running",
            detail="Cancel the existing job before starting a new one.",
        )


class InvalidJobStateTransitionError(CodeRebornError):
    """Raised when a job status transition is not allowed."""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(
            f"Cannot transition job from '{from_status}' to '{to_status}'"
        )


# ── Budget domain ────────────────────────────────────────────────────────────


class BudgetExceededError(CodeRebornError):
    """Raised when an LLM call would exceed the job's cost budget."""

    def __init__(self, current_cost: float, budget: float) -> None:
        super().__init__(
            f"LLM budget exceeded: ${current_cost:.4f} used of ${budget:.4f} budget",
            detail="Reduce analysis scope or increase the budget cap.",
        )
        self.current_cost = current_cost
        self.budget = budget


# ── Infrastructure ───────────────────────────────────────────────────────────


class DatabaseConnectionError(CodeRebornError):
    """Raised when the database is unreachable."""


class RedisConnectionError(CodeRebornError):
    """Raised when Redis is unreachable."""


# ── Repository / analysis ────────────────────────────────────────────────────


class RepositoryAccessError(CodeRebornError):
    """Raised when the target repository cannot be read or cloned."""

    def __init__(self, repo_url: str, reason: str) -> None:
        super().__init__(
            f"Cannot access repository '{repo_url}': {reason}"
        )


class StackDetectionError(CodeRebornError):
    """Raised when the StackDetector agent fails to produce a report."""


class AgentExecutionError(CodeRebornError):
    """Raised when a CrewAI agent task fails unexpectedly."""

    def __init__(self, agent_name: str, reason: str) -> None:
        super().__init__(f"Agent '{agent_name}' failed: {reason}")
        self.agent_name = agent_name
