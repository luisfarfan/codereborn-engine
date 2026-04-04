import json
import logging
from typing import Dict, Any
from pathlib import Path

from litellm import completion
from app.models.db_models import StackReport
from app.models.stack_models import PatternReport
from app.services.llm_budget_service import LLMBudgetService
from app.domain.enums import AnalysisMode

logger = logging.getLogger(__name__)

class PatternInterpreter:
    """
    Interpreter logic for Pattern Detector.
    Uses LLM to transform structural facts into architectural insights.
    """

    def __init__(self):
        self.prompt_path = Path("PROMPTS/pattern_detector.md")

    async def interpret(
        self, 
        job_id: str, 
        stack_report: StackReport,
        budget_service: LLMBudgetService
    ) -> PatternReport:
        """
        Calls the LLM to interpret the repository structure.
        """
        # 1. Prepare Context from Stack Report
        report_data = stack_report.report_data
        
        # 2. Load and Format Prompt
        system_prompt = self._load_prompt()
        user_content = self._format_user_prompt(report_data)

        # 3. Budget Check & Model Selection
        # Pattern Detector typically uses gpt-4o-mini (budget tier)
        # We can adjust based on AnalysisMode if needed
        model = "gpt-4o-mini"
        estimated_tokens = len(system_prompt + user_content) // 4 + 1000 # buffer for response
        
        budget_state = budget_service.get_state(job_id)
        if not budget_state:
             # Fallback if no state, though agent.py should have opened it
             budget_state = budget_service.open_job(job_id)
             
        evaluation = budget_service.evaluate(
            budget_state,
            agent="pattern_detector",
            model=model,
            estimated_tokens=estimated_tokens
        )
        
        if evaluation.approved_model is None:
            raise RuntimeError(f"LLM Call rejected by budget service: {evaluation.reason}")

        # 4. LLM Call
        try:
            response = completion(
                model=evaluation.approved_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            
            # 5. Record Spend
            actual_cost = response.get("_response_ms", 0) # This is dummy, LiteLLM usually returns cost in some fields
            # For now, we estimate or use litellm metadata if available
            cost_usd = getattr(response, "_hidden_params", {}).get("response_cost", 0.0)
            budget_service.record_actual_spend(budget_state, cost_usd)

            # 6. Parse and Validate
            content = response.choices[0].message.content
            raw_json = json.loads(content)
            
            # Enrich with metadata
            raw_json["llm_model_used"] = evaluation.approved_model
            raw_json["tokens_used"] = response.usage.total_tokens
            raw_json["cost_usd"] = cost_usd
            
            return PatternReport(**raw_json)

        except Exception as e:
            logger.error(f"LLM interpretation failed: {str(e)}")
            raise

    def _load_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found at {self.prompt_path}")
        return self.prompt_path.read_text()

    def _format_user_prompt(self, data: Dict[str, Any]) -> str:
        # Extract key structural facts for the LLM
        inventory = data.get("file_inventory", {})
        structure = data.get("directory_structure", {})
        
        # Simplified view of directories for the prompt
        dirs_summary = []
        for d in structure.get("root_directories", []):
            dirs_summary.append({
                "path": d["path"],
                "subdirectories": d["subdirectories"],
                "file_count": d["file_count"],
                "file_breakdown": d["file_breakdown"]
            })

        user_context = {
            "project_name": data.get("project_name", "unknown"),
            "primary_language": data.get("primary_language", "unknown"),
            "frameworks": [f["name"] for f in data.get("frameworks", [])],
            "analysis_scope": data.get("analysis_scope", "other"),
            "total_files": inventory.get("total_files", 0),
            "language_breakdown": data.get("languages", []),
            "directory_structure_summary": dirs_summary
        }
        
        return f"Structure Data:\n{json.dumps(user_context, indent=2)}\n\nInterpret the patterns according to the specification."
