"""
SignalInterpreter - Layer 3: LLM Zero-shot signal extraction fallback.
Used when Tree-sitter or LSP is not available for a given file/language.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session

from app.models.stack_models import UniversalSignalFormat, SignalDeclaration
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
        Currently a placeholder that returns minimal signals or None
        to avoid unexpected LLM costs during initial pipeline verification.
        """
        logger.info(f"Layer 3: Interpreting file {file_path} (Language: {language}) via LLM fallback...")
        
        # TODO: Implement real LLM zero-shot extraction logic here
        # For now, we return None to indicate no signals extracted via LLM
        # to prevent consumption of budget in early testing phases.
        
        return None
