import json
import logging
from typing import Dict, Any, List
from litellm import acompletion

from app.core.settings import get_settings
from app.services.llm_budget_service import LLMBudgetService, JobBudgetState
from app.domain.enums import LLMDecision

logger = logging.getLogger(__name__)
settings = get_settings()

class ArchitecturalInductor:
    """
    Induces the project-specific architectural 'DNA' using a cheap LLM.
    Generates dynamic classification rules based on technical signals.
    """

    SYSTEM_PROMPT = """
    You are an Expert Software Architect. Your mission is to 'Induce' the architectural patterns 
    of a codebase based on a 'Technical DNA Snapshot' (imports, decorators, etc.) and its file tree.

    Analyze the provided metadata and return a JSON schema that defines how to classify files.
    Focus on standard roles: entrypoint, controller, service, repository, model, dto, test, utility.

    ### JSON Response Format:
    {
      "framework_conventions": ["string description of detected patterns"],
      "assignment_rules": [
        {
          "if_signal": "string (regex or exact match of an import/decorator)",
          "signal_type": "import | decorator | extension | path",
          "assign_role": "string (the architectural role)",
          "confidence": 0.0-1.0
        }
      ],
      "zone_rules": [
        {
          "dir_path": "string",
          "assign_role": "string",
          "confidence": 0.0-1.0
        }
      ]
    }
    """

    def __init__(self, budget_service: LLMBudgetService):
        self.budget_service = budget_service

    async def induce(
        self, 
        job_id: str, 
        dna_snapshot: Dict[str, Any], 
        tree_summary: List[Dict[str, Any]],
        stack_report: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Calls the LLM to generate the classification schema.
        """
        budget_state = self.budget_service.get_state(job_id)
        if not budget_state:
            # Fallback to default rules if no budget tracking (shouldn't happen in production)
            logger.warning(f"No budget state found for job {job_id}. Using default empty schema.")
            return self._get_empty_schema()

        # 1. Evaluate Budget
        model = settings.LLM_PREFERRED_MODEL # gpt-4o-mini
        evaluation = self.budget_service.evaluate(
            budget_state, 
            agent="architecture_context_builder", 
            model=model, 
            estimated_tokens=4000 # Estimate context size
        )

        if evaluation.decision == LLMDecision.REJECT:
            logger.error(f"LLM induction rejected for job {job_id}: {evaluation.reason}")
            return self._get_empty_schema()

        # 2. Prepare Prompt
        user_prompt = f"""
        ### Stack Report:
        {json.dumps(stack_report, indent=2) if stack_report else "Unknown"}

        ### Technical DNA Snapshot:
        - Extensions: {dna_snapshot.get('file_extensions')}
        - Top Imports/Libs: {dna_snapshot.get('top_imports')}
        - Detectors/Decorators: {dna_snapshot.get('detected_decorators')}
        - Base Classes/Interfaces: {dna_snapshot.get('detected_base_classes')}

        ### File Tree Summary (Zones):
        {json.dumps(tree_summary[:20], indent=2)}
        """

        try:
            response = await acompletion(
                model=evaluation.approved_model or model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            # 3. Record Spend
            cost = response.get("_response_ms", 0) / 1000 * 0.00015 # Very rough estimate if cost not provided
            actual_cost = getattr(response, "cost", cost)
            self.budget_service.record_actual_spend(budget_state, actual_cost)

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.exception(f"Induction LLM call failed for job {job_id}: {e}")
            return self._get_empty_schema()

    def _get_empty_schema(self) -> Dict[str, Any]:
        return {
            "framework_conventions": [],
            "assignment_rules": [],
            "zone_rules": []
        }
