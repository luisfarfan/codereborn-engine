"""
UniversalExtractorAgent - Orchestrator for Multi-Layer Signal Extraction.
Follows the decision tree strategy: Tree-sitter -> LSP -> LLM -> Pattern Mining.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session

from app.agents.universal_extractor.registry import GrammarRegistry
from app.agents.universal_extractor.extractor import SignalExtractor
# Layer 3 fallback
from app.agents.universal_extractor.interpreter import SignalInterpreter
from app.models.stack_models import StackIntelligenceReport, PatternReport, SignalExtractionReport, ExtractionSummary, CostBreakdown
from app.services.llm_budget_service import LLMBudgetService

logger = logging.getLogger(__name__)

# Config paths
GRAMMARS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "grammars"))

class UniversalExtractorAgent:
    """
    Agent responsible for extracting structural signals using the best available layer.
    """

    def __init__(self, budget_service: LLMBudgetService):
        self.registry = GrammarRegistry(GRAMMARS_DIR)
        self.extractor = SignalExtractor(self.registry)
        self.interpreter = SignalInterpreter(budget_service)
        self.budget_service = budget_service

    async def execute(self, 
                    job_id: Any, 
                    repo_path: str,
                    stack_report: StackIntelligenceReport,
                    pattern_report: PatternReport,
                    db_session: Session) -> SignalExtractionReport:
        """
        Executes signal extraction for the chosen sample of files.
        Standard Orchestration Flow: Layer 1 -> Layer 2 -> Layer 3 -> Layer 4.
        """
        
        logger.info(f"🚀 Job {job_id}: Starting Universal Signal Extraction...")
        start_time = datetime.utcnow()
        
        # 1. SELECT FILES TO ANALYZE (Based on Pattern Detector sampling)
        files_to_analyze = self._select_files(repo_path, pattern_report)
        
        results_by_file = {}
        strategy_counts = {"tree-sitter": 0, "llm_zero_shot": 0, "lsp": 0, "pattern_mining": 0}
        language_counts = {}
        total_llm_cost = 0.0

        # 2. EXTRACTION LOOP (Applying layers)
        for rel_path in files_to_analyze:
            ext = os.path.splitext(rel_path)[1]
            lang = self.registry.resolve_language_by_extension(ext)
            
            signal_data = None
            
            # --- LAYER 1: Tree-sitter (Deterministic, $0) ---
            if self.registry.has_grammar(lang):
                signal_data = await self.extractor.extract_from_file(rel_path, repo_path)
                if signal_data:
                    strategy_counts["tree-sitter"] += 1
            
            # --- LAYER 2: LSP (Premium Tier placeholder) ---
            # TODO: Placeholder for LSP logic when tier allows it.

            # --- LAYER 3: LLM Zero-shot (Fallback) ---
            if not signal_data:
                # LLM interpretation follows specific budget constraints
                signal_data = await self.interpreter.analyze_file(rel_path, lang, repo_path, job_id, db_session)
                if signal_data:
                    strategy_counts["llm_zero_shot"] += 1
                    total_llm_cost += signal_data.metadata.get("cost_usd", 0.0)

            # --- RECORD RESULTS ---
            if signal_data:
                results_by_file[rel_path] = signal_data
                language_counts[lang] = language_counts.get(lang, 0) + 1
            else:
                logger.warning(f"Failed to extract signals from {rel_path} using any available layer.")

        # 3. BUILD FINAL REPORT
        summary = ExtractionSummary(
            total_files_analyzed=len(results_by_file),
            total_files_in_repo=stack_report.report_data.get("file_inventory", {}).get("total_files", 0),
            extraction_strategies_used=strategy_counts,
            languages_analyzed=language_counts,
            sampling_applied=True,
            sampling_ratio=len(results_by_file) / (stack_report.report_data.get("file_inventory", {}).get("total_files", 1))
        )

        return SignalExtractionReport(
            extraction_summary=summary,
            signals_by_file=results_by_file,
            global_patterns={}, # Optimized in Phase 2
            cost_breakdown=CostBreakdown(
                total_cost_usd=self.budget_service.get_state(str(job_id)).spent_usd,
                llm_cost=self.budget_service.get_state(str(job_id)).spent_usd,
                tree_sitter_cost=0.0,
                lsp_cost=0.0,
                pattern_generation_cost=0.0
            ),
            analysis_metadata={
                "analysis_duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_version": "1.2.0 (Dynamic Decision Engine)"
            }
        )

    def _select_files(self, repo_path: str, pattern_report: PatternReport) -> List[str]:
        """Samples representative files based on Pattern Detection rules."""
        selected = []
        rules = pattern_report.sampling_strategy.sampling_rules or {}
        supported_exts = tuple(self.registry.get_supported_extensions())
        
        # 1. Process explicit Rules from Sampling Strategy
        for dir_path, rule in rules.items():
            if rule.strategy == "skip":
                continue
            
            dir_full = os.path.join(repo_path, dir_path)
            if not (os.path.exists(dir_full) and os.path.isdir(dir_full)):
                continue

            # Get all candidate files in directory (recursively)
            candidates = []
            for root, _, files in os.walk(dir_full):
                for f in files:
                    if f.endswith(supported_exts):
                        full_f = os.path.join(root, f)
                        rel_f = os.path.relpath(full_f, repo_path)
                        candidates.append(rel_f)

            if rule.strategy == "analyze_all":
                # Take everything in this critical directory
                selected.extend(candidates)
            elif rule.strategy == "sample":
                # Take a sample based on Phase 2 recommendation
                # Sanitization: ensure at least 1 if not empty, default to 5 if 0 or None
                sample_size = rule.sample_size or 5
                if sample_size <= 0 and candidates:
                    sample_size = 1
                selected.extend(candidates[:sample_size])
        
        # 2. Fallback: if no rules yielded files, try to find some code files in high-priority dirs
        if not selected:
            high_priority_dirs = [
                path for path, meta in pattern_report.directory_interpretation.items()
                if getattr(meta, "priority", "low") == "high"
            ]
            for d in high_priority_dirs:
                dir_full = os.path.join(repo_path, d)
                if os.path.exists(dir_full) and os.path.isdir(dir_full):
                    for f in os.listdir(dir_full)[:10]:
                        if f.endswith(supported_exts):
                            selected.append(os.path.join(d, f))
        
        # 3. Final verification and deduplication
        verified = []
        seen = set()
        for f in selected:
            if f not in seen and os.path.exists(os.path.join(repo_path, f)):
                verified.append(f)
                seen.add(f)
        
        # Honor recommended_sample_size but with a sane minimum for large repos
        rec_size = pattern_report.sampling_strategy.recommended_sample_size or 50
        global_limit = max(100, rec_size)
        
        return verified[:global_limit]
