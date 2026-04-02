"""
LLMBudgetService — gatekeeper for all LLM calls in the pipeline.

Responsibilities:
  1. Evaluate whether a proposed LLM call fits within the job's budget.
  2. Optionally downgrade to a cheaper model when budget is tight.
  3. Log every decision to the llm_call_decisions table for audit/analysis.

Decision logic (rule-based, not ML):
  - If estimated_cost + current_spend <= budget     → APPROVE
  - If 80%+ of budget used but call can be cheaper  → DOWNGRADE to economy model
  - If budget would be exceeded even with cheapest  → REJECT

This service is intentionally free of framework dependencies so it can be
unit-tested without a running database or network.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import AnalysisMode, LLMDecision

# Cost estimates in USD per 1K tokens (input + output blended avg)
MODEL_COSTS_PER_1K: dict[str, float] = {
    "gpt-4o": 0.010,
    "gpt-4o-mini": 0.000300,
    "claude-3-5-sonnet-20241022": 0.009,
    "claude-3-haiku-20240307": 0.000375,
    "gemini-1.5-pro": 0.007,
    "gemini-1.5-flash": 0.000188,
}

ECONOMY_MODELS: dict[AnalysisMode, str] = {
    AnalysisMode.ECONOMY: "gpt-4o-mini",
    AnalysisMode.BALANCED: "gpt-4o-mini",
    AnalysisMode.QUALITY: "claude-3-haiku-20240307",
}


@dataclass
class BudgetEvaluation:
    decision: LLMDecision
    approved_model: str | None
    estimated_cost_usd: float
    budget_remaining_usd: float
    reason: str


@dataclass
class JobBudgetState:
    """In-memory budget tracker for a single job."""

    job_id: str
    max_usd: float
    mode: AnalysisMode
    spent_usd: float = 0.0
    call_count: int = 0
    decisions: list[BudgetEvaluation] = field(default_factory=list)

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.max_usd - self.spent_usd)

    @property
    def utilization(self) -> float:
        return self.spent_usd / self.max_usd if self.max_usd > 0 else 0.0


class LLMBudgetService:
    """
    Evaluate and track LLM costs for analysis jobs.

    Usage:
        service = LLMBudgetService(default_budget_usd=0.50, max_budget_usd=5.00)
        budget = service.open_job(job_id="abc", max_usd=1.00, mode=AnalysisMode.BALANCED)
        evaluation = service.evaluate(budget, agent="stack_detector", model="gpt-4o", est_tokens=2000)
        if evaluation.decision != LLMDecision.REJECT:
            # call LLM with evaluation.approved_model
            service.record_actual_spend(budget, actual_cost_usd=0.004)
    """

    def __init__(self, default_budget_usd: float = 0.50, max_budget_usd: float = 5.00) -> None:
        self.default_budget_usd = default_budget_usd
        self.max_budget_usd = max_budget_usd
        self._states: dict[str, JobBudgetState] = {}

    def open_job(
        self,
        job_id: str,
        max_usd: float | None = None,
        mode: AnalysisMode = AnalysisMode.BALANCED,
    ) -> JobBudgetState:
        """Initialize budget tracking for a new job."""
        capped = min(max_usd or self.default_budget_usd, self.max_budget_usd)
        state = JobBudgetState(job_id=job_id, max_usd=capped, mode=mode)
        self._states[job_id] = state
        return state

    def get_state(self, job_id: str) -> JobBudgetState | None:
        return self._states.get(job_id)

    def evaluate(
        self,
        state: JobBudgetState,
        agent: str,
        model: str,
        estimated_tokens: int,
    ) -> BudgetEvaluation:
        """
        Decide whether to approve, downgrade, or reject an LLM call.
        Does NOT mutate state — call record_actual_spend() after the real call.
        """
        cost_per_1k = MODEL_COSTS_PER_1K.get(model, 0.010)
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k

        if state.spent_usd + estimated_cost <= state.remaining_usd + state.spent_usd:
            # Fits in budget
            if state.utilization >= 0.80:
                # Budget is 80%+ used — try downgrade first
                economy_model = ECONOMY_MODELS.get(state.mode, "gpt-4o-mini")
                economy_cost = (estimated_tokens / 1000) * MODEL_COSTS_PER_1K.get(economy_model, 0.0003)
                if state.spent_usd + economy_cost <= state.max_usd:
                    ev = BudgetEvaluation(
                        decision=LLMDecision.DOWNGRADE,
                        approved_model=economy_model,
                        estimated_cost_usd=economy_cost,
                        budget_remaining_usd=state.remaining_usd,
                        reason=f"Budget {state.utilization:.0%} used; downgraded {model} → {economy_model}",
                    )
                    state.decisions.append(ev)
                    return ev

            ev = BudgetEvaluation(
                decision=LLMDecision.APPROVE,
                approved_model=model,
                estimated_cost_usd=estimated_cost,
                budget_remaining_usd=state.remaining_usd,
                reason="Within budget",
            )
            state.decisions.append(ev)
            return ev

        ev = BudgetEvaluation(
            decision=LLMDecision.REJECT,
            approved_model=None,
            estimated_cost_usd=estimated_cost,
            budget_remaining_usd=state.remaining_usd,
            reason=(
                f"Would cost ${estimated_cost:.4f} but only "
                f"${state.remaining_usd:.4f} remains of ${state.max_usd:.4f} budget"
            ),
        )
        state.decisions.append(ev)
        return ev

    def record_actual_spend(self, state: JobBudgetState, actual_cost_usd: float) -> None:
        """Update the job's running total after a real LLM call completes."""
        state.spent_usd += actual_cost_usd
        state.call_count += 1

    def close_job(self, job_id: str) -> JobBudgetState | None:
        """Remove a job's budget state and return the final summary."""
        return self._states.pop(job_id, None)
