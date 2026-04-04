"""
LLMBudgetService — Gatekeeper for all LLM calls in the pipeline.

Responsibilities:
  1. Evaluate whether a proposed LLM call fits within the job's budget.
  2. Persist every decision to the `llm_call_decisions` table.
  3. Track cumulative spend in the `jobs` table.

This version is the 'baseline' implementation, using hardcoded costs
compatible with OpenRouter/Gemini.
"""

import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.enums import LLMDecision
from app.models.db_models import Job, LLMCallDecision


# Cost estimates in USD per 1K tokens (Blended input/output for simplicity)
# Rates based on OpenRouter / Google Gemini Flash Lite
MODEL_COSTS_PER_1K: dict[str, float] = {
    "openrouter/google/gemini-2.0-flash-lite-001": 0.0001,  # Est. $0.10 per 1M
    "google/gemini-2.0-flash-lite-001": 0.0001,
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
}

# Free models are explicitly mapped to 0.0
FREE_MODELS = [
    "openrouter/google/gemini-2.0-flash-lite-preview-001:free",
]


class LLMBudgetService:
    """
    Handles LLM budget evaluation and persistence.
    Simplified version for initial CodeReborn Engine integration.
    """

    def __init__(self, default_budget_usd: float = 0.50, max_budget_usd: float = 5.00) -> None:
        self.default_budget_usd = default_budget_usd
        self.max_budget_usd = max_budget_usd

    async def evaluate_and_record(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        agent_name: str,
        model: str,
        estimated_tokens: int,
    ) -> LLMCallDecision:
        """
        Main entry point: Evaluates if a call is affordable AND persists the decision.
        """
        # 1. Get current job state
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # 2. Calculate estimated cost
        cost_per_1k = MODEL_COSTS_PER_1K.get(model, 0.001)  # Default $1/1M if unknown
        if model in FREE_MODELS:
            cost_per_1k = 0.0

        estimated_cost = (estimated_tokens / 1000) * cost_per_1k

        # 3. Determine remaining budget
        # budget_config usually contains {"max_usd": 1.0}
        max_usd = job.budget_config.get("max_usd", self.default_budget_usd) \
            if job.budget_config else self.default_budget_usd
        remaining = max_usd - job.cost_usd

        # 4. Make decision
        decision_val = LLMDecision.APPROVE
        reason = "Within budget"
        approved_model = model

        if estimated_cost > remaining:
            decision_val = LLMDecision.REJECT
            reason = f"Insufficient budget: needs ${estimated_cost:.4f}, has ${remaining:.4f}"
            approved_model = None

        # 5. Persist the decision
        decision = LLMCallDecision(
            job_id=job_id,
            agent_name=agent_name,
            requested_model=model,
            approved_model=approved_model,
            decision=decision_val,
            estimated_cost_usd=estimated_cost,
            budget_remaining_usd=remaining,
            reason=reason
        )
        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        return decision

    async def update_job_spend(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        actual_cost_usd: float,
        tokens_used: int = 0,
        model_used: str | None = None
    ) -> None:
        """
        Call this AFTER a successful LLM interaction to update totals.
        """
        job = await session.get(Job, job_id)
        if job:
            job.cost_usd += actual_cost_usd
            job.tokens_used += tokens_used
            if model_used and model_used not in job.models_used:
                # SQLModel JSONB fields need manual trickery sometimes or just replace
                new_models = list(job.models_used)
                new_models.append(model_used)
                job.models_used = new_models

            session.add(job)
            await session.commit()
