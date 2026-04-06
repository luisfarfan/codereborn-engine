"""
SignalInterpreter - Layer 3: LLM Zero-shot signal extraction fallback.
Used when Tree-sitter or LSP is not available for a given file/language.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.models.stack_models import SignalDeclaration, UniversalSignalFormat
from app.services.llm_budget_service import LLMBudgetService

logger = logging.getLogger(__name__)

class SignalInterpreter:
    """
    Fallback extraction layer using LLM zero-shot analysis.
    Useful for languages without established Tree-sitter grammars
    or files with parsing errors.
    """

    def __init__(self, budget_service: LLMBudgetService):
        self.budget_service = budget_service

    async def analyze_file(self, 
                           file_path: str, 
                           language: str, 
                           repo_path: str, 
                           job_id: Any, 
                           db_session: Session) -> Optional[UniversalSignalFormat]:
        """
        Analyzes a file using an LLM to extract signals.
        This provides a high-confidence fallback when AST extraction fails.
        """
        logger.info(f"Layer 3: Interpreting file {file_path} (Language: {language}) via LLM fallback...")
        
        full_path = os.path.join(repo_path, file_path)
        try:
            with open(full_path, "r", encoding="utf8") as f:
                content = f.read()
        except:
            return None

        # 1. Budget Evaluation
        # We assume 1000 input tokens for a typical file + 500 output tokens
        est_tokens = len(content.split()) + 500
        decision = self.budget_service.evaluate(
            state=self.budget_service.get_state(str(job_id)),
            agent="signal_interpreter",
            model="google/gemini-2.0-flash-lite-001",
            estimated_tokens=est_tokens
        )
        
        if decision.decision == "reject":
            logger.warning(f"Budget rejected for LLM fallback on {file_path}")
            return None
            
        model_to_use = decision.approved_model or "google/gemini-2.0-flash-lite-001"
        # LiteLLM via OpenRouter requires the 'openrouter/' prefix unless it's a native provider
        if not model_to_use.startswith("openrouter/"):
            model_to_use = f"openrouter/{model_to_use}"

        # 2. LLM Call
        prompt = f"""
        Extract architectural signals from the following {language} file: {file_path}
        
        Analyze imports, classes, functions, and decorators.
        
        Output valid JSON only with this structure:
        {{
            "imports": ["..."],
            "class_declarations": [{{ "name": "...", "line_number": 0, "is_exported": true }}],
            "function_declarations": [{{ "name": "...", "line_number": 0, "is_exported": true }}],
            "decorators": ["..."],
            "type_definitions": ["..."]
        }}
        
        CODE:
        {content}
        """
        
        try:
            import litellm
            response = await litellm.acompletion(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Record cost
            # LiteLLM usually provides cost in response.usage.total_cost if supported
            actual_cost = getattr(response, "usage", {}).get("total_cost", 0.0) or 0.0001
            self.budget_service.record_actual_spend(self.budget_service.get_state(str(job_id)), actual_cost)
            
            raw_data = response.choices[0].message.content
            import json
            data = json.loads(raw_data)
            
            # Map to structures
            def to_decl(d):
                if isinstance(d, str):
                    return SignalDeclaration(name=d, is_exported=True)
                return SignalDeclaration(**d)

            signals = {
                "imports": [to_decl(x) for x in data.get("imports", [])],
                "class_declarations": [to_decl(x) for x in data.get("class_declarations", [])],
                "function_declarations": [to_decl(x) for x in data.get("function_declarations", [])],
                "decorators": [to_decl(x) for x in data.get("decorators", [])],
                "type_definitions": [to_decl(x) for x in data.get("type_definitions", [])],
                "file_dependencies": []
            }

            return UniversalSignalFormat(
                file_path=file_path,
                language=language,
                extraction_method="llm-zero-shot",
                signals=signals,
                metadata={
                    "lines_of_code": len(content.splitlines()),
                    "confidence": 0.8,
                    "extraction_timestamp": datetime.utcnow().isoformat(),
                    "cost_usd": actual_cost
                }
            )

        except Exception as e:
            logger.error(f"LLM extraction failed for {file_path}: {e}")
            return None
