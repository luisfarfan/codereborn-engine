"""
LLMBudgetService — Gatekeeper for all LLM calls in the pipeline.

Responsibilities:
  1. Evaluate whether a proposed LLM call fits within the job's budget.
  2. Persist every decision to the `llm_call_decisions` table.
  3. Track cumulative spend in the `jobs` table.

This version is the 'baseline' implementation, using hardcoded costs
compatible with OpenRouter/Gemini.
"""

import logging
import uuid
from typing import Any

from openrouter_insights import LLMIndexSync
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.enums import LLMDecision
from app.models.db_models import Job, LLMCallDecision

logger = logging.getLogger(__name__)

class LLMBudgetService:
    """
    Handles LLM budget evaluation and persistence using openrouter-insights
    for dynamic model intelligence and pricing.
    """

    def __init__(self, default_budget_usd: float = 0.50, max_budget_usd: float = 5.00) -> None:
        self.default_budget_usd = default_budget_usd
        self.max_budget_usd = max_budget_usd
        self._states: dict[str, Any] = {}
        
        # Initialize the global LLM index (offline-first mode)
        try:
            self.index = LLMIndexSync(mode="json")
            logger.info("LLMBudgetService: Dynamic model index initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize LLMIndexSync: {e}")
            self.index = None

    def get_state(self, job_id: str) -> Any | None:
        """Returns the in-memory state for a job."""
        return self._states.get(job_id)

    def open_job(self, job_id: str, max_usd: float | None = None, mode: str | None = None) -> Any:
        """Synchronous job opening for backward compatibility."""
        max_usd = min(max_usd or self.default_budget_usd, self.max_budget_usd)
        state = type('BudgetState', (object,), {
            'job_id': job_id,
            'max_usd': max_usd,
            'spent_usd': 0.0,
            'call_count': 0,
            'mode': mode
        })
        self._states[job_id] = state
        return state

    def _get_model_cost_per_1k(self, model_id: str) -> float:
        """Helper to get blended cost per 1K tokens from the index."""
        if not self.index:
            return 0.001
            
        model = self.index.get_model(model_id)
        if not model or not model.pricing:
            return 0.001
            
        # Pricing in index (0.6.0+) is per 1M tokens. 
        # Built-in filtering now handles openrouter/auto and negative prices.
        blended_1m = (model.pricing.input * 0.7) + (model.pricing.output * 0.3)
        return blended_1m / 1000.0

    def evaluate(self, state: Any, agent: str, model: str, estimated_tokens: int) -> Any:
        """
        Evaluate if the call is affordable.
        Uses openrouter-insights 0.6.0 for smart fallback selection.
        """
        cost_per_1k = self._get_model_cost_per_1k(model)
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k
        remaining = state.max_usd - state.spent_usd
        
        decision = LLMDecision.APPROVE
        reason = "Within budget"
        approved_model = model

        if estimated_cost > remaining:
            logger.info(f"Budget exceeded for {model} (${estimated_cost:.4f} > ${remaining:.4f}).")
            
            # Use 0.6.0's get_best_alternative()
            # max_price is in USD per 1M tokens in the library
            max_price_1m = (remaining / estimated_tokens) * 1_000_000
            
            fallback = None
            if self.index:
                fallback = self.index.get_best_alternative(model, max_price=max_price_1m)
            
            if fallback:
                decision = LLMDecision.DOWNGRADE
                reason = f"Original model too expensive. Downgraded to {fallback.id}."
                approved_model = fallback.id
            else:
                decision = LLMDecision.REJECT
                reason = f"Insufficient budget: needs ${estimated_cost:.4f}, has ${remaining:.4f}. No smart alternative found."
                approved_model = None

        return type('Decision', (object,), {
            'decision': decision,
            'approved_model': approved_model,
            'reason': reason
        })

    def record_actual_spend(self, state: Any, actual_cost_usd: float) -> None:
        """Record the actual cost after the LLM call completes."""
        state.spent_usd += actual_cost_usd
        state.call_count += 1

    async def evaluate_and_record(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        agent_name: str,
        model: str,
        estimated_tokens: int,
    ) -> LLMCallDecision:
        """
        Async version with persistence.
        """
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Reuse the sync evaluate logic
        state = type('State', (object,), {
            'max_usd': job.budget_config.get("max_usd", self.default_budget_usd) if job.budget_config else self.default_budget_usd,
            'spent_usd': job.cost_usd
        })
        
        eval_res = self.evaluate(state, agent_name, model, estimated_tokens)

        # Persist the decision
        decision = LLMCallDecision(
            job_id=job_id,
            agent_name=agent_name,
            requested_model=model,
            approved_model=eval_res.approved_model,
            decision=eval_res.decision,
            estimated_cost_usd=(estimated_tokens / 1000) * self._get_model_cost_per_1k(model),
            budget_remaining_usd=state.max_usd - state.spent_usd,
            reason=eval_res.reason
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
