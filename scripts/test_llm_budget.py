import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.llm_budget_service import LLMBudgetService
from app.domain.enums import LLMDecision

def test_budget_service():
    print("🧪 Testing LLMBudgetService with openrouter-insights...")
    
    # Ensure index exists
    index_path = Path("app/services/llm_index.json")
    if not index_path.exists():
        print("❌ Error: llm_index.json not found. Run scripts/sync_llms.py first.")
        return

    service = LLMBudgetService()
    
    # 1. Test standard approval
    print("\nCase 1: Standard Approval (Gemini Flash Lite, $0.10 budget)")
    state = service.open_job("test-job-1", max_usd=0.10)
    eval1 = service.evaluate(
        state, 
        agent="test", 
        model="google/gemini-2.0-flash-lite-001", 
        estimated_tokens=5000
    )
    print(f"Decision: {eval1.decision}")
    print(f"Approved Model: {eval1.approved_model}")
    print(f"Reason: {eval1.reason}")
    assert eval1.decision == LLMDecision.APPROVE

    # 2. Test Downgrade
    print("\nCase 2: Downgrade (GPT-4o requested with $0.001 budget)")
    state2 = service.open_job("test-job-2", max_usd=0.001)
    # GPT-4o is expensive
    eval2 = service.evaluate(
        state2, 
        agent="test", 
        model="openai/gpt-4o", 
        estimated_tokens=10000
    )
    print(f"Decision: {eval2.decision}")
    print(f"Approved Model: {eval2.approved_model}")
    print(f"Reason: {eval2.reason}")
    assert eval2.decision == LLMDecision.DOWNGRADE

    # 3. Test Rejection
    print("\nCase 3: Rejection (Huge request with tiny budget)")
    state3 = service.open_job("test-job-3", max_usd=0.00001)
    eval3 = service.evaluate(
        state3, 
        agent="test", 
        model="openai/gpt-4o", 
        estimated_tokens=50000
    )
    print(f"Decision: {eval3.decision}")
    print(f"Reason: {eval3.reason}")
    assert eval3.decision == LLMDecision.REJECT

    print("\n✅ All Budget Service tests passed!")

if __name__ == "__main__":
    test_budget_service()
