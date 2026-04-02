"""
Unit tests for LLMBudgetService.

These are pure unit tests — no DB, no HTTP, just logic.
"""

import pytest

from app.domain.enums import AnalysisMode, LLMDecision
from app.services.llm_budget_service import LLMBudgetService


@pytest.fixture
def service():
    return LLMBudgetService(default_budget_usd=1.00, max_budget_usd=5.00)


def test_approve_within_budget(service):
    state = service.open_job("job-1", max_usd=1.00, mode=AnalysisMode.BALANCED)
    ev = service.evaluate(state, agent="stack_detector", model="gpt-4o-mini", estimated_tokens=500)
    assert ev.decision == LLMDecision.APPROVE
    assert ev.approved_model == "gpt-4o-mini"


def test_reject_over_budget(service):
    state = service.open_job("job-2", max_usd=0.001, mode=AnalysisMode.BALANCED)
    ev = service.evaluate(state, agent="stack_detector", model="gpt-4o", estimated_tokens=10_000)
    assert ev.decision == LLMDecision.REJECT
    assert ev.approved_model is None


def test_record_spend_accumulates(service):
    state = service.open_job("job-3", max_usd=1.00)
    service.record_actual_spend(state, actual_cost_usd=0.30)
    service.record_actual_spend(state, actual_cost_usd=0.25)
    assert round(state.spent_usd, 2) == 0.55
    assert state.call_count == 2


def test_max_budget_cap_enforced(service):
    state = service.open_job("job-4", max_usd=100.00)
    assert state.max_usd == 5.00  # capped at max_budget_usd


def test_close_job_removes_state(service):
    service.open_job("job-5", max_usd=1.00)
    result = service.close_job("job-5")
    assert result is not None
    assert service.get_state("job-5") is None
