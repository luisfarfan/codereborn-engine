import json
import logging
from pathlib import Path
from typing import Any, Dict

from litellm import completion

from app.models.db_models import StackReport
from app.models.stack_models import PatternReport
from app.services.llm_budget_service import LLMBudgetService

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

        # 3. Model Selection (Using OpenRouter Stable Model)
        model = "openrouter/google/gemini-2.0-flash-lite-001"
        estimated_tokens = len(system_prompt + user_content) // 4 + 1000
        
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
            # For free models, cost is 0.0
            cost_usd = 0.0
            if ":free" not in evaluation.approved_model:
                cost_usd = getattr(response, "_hidden_params", {}).get("response_cost", 0.0)
            
            budget_service.record_actual_spend(budget_state, cost_usd)

            # 6. Parse and Validate
            content = response.choices[0].message.content
            
            # Robust JSON extraction from Markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            raw_json = json.loads(content.strip())
            
            # Ensure metadata matches PatternReport schema (AnalysisMetadata)
            # The LLM often puts metadata at the root or within analysis_metadata
            metadata = raw_json.get("analysis_metadata", {})
            metadata["llm_model_used"] = evaluation.approved_model
            metadata["tokens_used"] = response.usage.total_tokens
            metadata["cost_usd"] = cost_usd
            
            # Ensure root confidence_score exists for Pydantic
            if "confidence_score" not in raw_json:
                # Try to get it from nested objects if present
                raw_json["confidence_score"] = metadata.get("confidence_score") or \
                    raw_json.get("detected_patterns", {}).get("confidence", 1.0)
            
            raw_json["analysis_metadata"] = metadata
            
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
