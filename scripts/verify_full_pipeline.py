import asyncio
import uuid
import logging
import argparse
import json
from app.infrastructure.database import AsyncSessionFactory
from app.agents.stack_detector.agent import StackDetectorAgent
from app.agents.pattern_detector.agent import PatternDetectorAgent
from app.agents.universal_extractor.agent import UniversalExtractorAgent
from app.services.llm_budget_service import LLMBudgetService
from app.domain.enums import AnalysisScope

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipeline(repo_path: str):
    """
    Orchestrates Phase 1 and Phase 2 on a real repository path.
    """
    async with AsyncSessionFactory() as session:
        job_id = uuid.uuid4()
        logger.info(f"🚀 Starting Full Pipeline Verification for Job: {job_id}")

        # PHASE 1: Stack Detector (Deterministic)
        logger.info("\n--- [PHASE 1: STACK DETECTOR] ---")
        try:
            stack_agent = StackDetectorAgent(session)
            stack_report = await stack_agent.execute(job_id, repo_path)
            logger.info(f"✅ Stack Detector completed.")
            
            # Access from report_data dict
            data = stack_report.report_data
            logger.info(f"Project: {data.get('project_name', 'unknown')}")
            logger.info(f"Primary Language: {stack_report.primary_language}")
            
            total_files = data.get('file_inventory', {}).get('total_files', 0)
            logger.info(f"Files Inventoried: {total_files}")
        except Exception as e:
            logger.error(f"❌ Phase 1 failed: {str(e)}")
            return

        # PHASE 2: Pattern Detector (LLM Interpretation)
        logger.info("\n--- [PHASE 2: PATTERN DETECTOR] ---")
        try:
            pattern_agent = PatternDetectorAgent(session)
            pattern_report = await pattern_agent.execute(job_id, repo_path)
            
            logger.info(f"✅ Pattern Detector completed!")
            logger.info(f"Detected Architecture: {pattern_report.detected_patterns.primary_pattern}")
            logger.info(f"Confidence: {pattern_report.detected_patterns.confidence*100:.1f}%")
            logger.info(f"Recommended Sample Size: {pattern_report.sampling_strategy.recommended_sample_size} files")
            
            # Save final unified result for inspection
            output_file = "pipeline_result.json"
            with open(output_file, "w") as f:
                # Combine both data for the user to see
                combined = {
                    "job_id": str(job_id),
                    "stack_intelligence": stack_report.model_dump(mode="json"),
                    "architectural_interpretation": pattern_report.model_dump(mode="json")
                }
                json.dump(combined, f, indent=2)
            
            logger.info(f"\n📄 Architectural report saved to '{output_file}'")
            
            # PHASE 3: Universal Signal Extractor (Hybrid Extraction)
            logger.info("\n--- [PHASE 3: SIGNAL EXTRACTOR] ---")
            try:
                # 1. Initialize agent and budget service (baseline)
                budget_service = LLMBudgetService()
                budget_service.open_job(str(job_id)) # CRITICAL: Open job state for Phase 3!
                signal_agent = UniversalExtractorAgent(budget_service)
                
                # Execute extraction (sampling from pattern_report)
                logger.info(f"Extracting signals from {repo_path}...")
                signal_report = await signal_agent.execute(
                    job_id=job_id,
                    repo_path=repo_path,
                    stack_report=stack_report,
                    pattern_report=pattern_report,
                    db_session=session
                )
                
                logger.info(f"✅ Signal Extractor completed!")
                summary = signal_report.extraction_summary
                logger.info(f"Files Analyzed: {summary.total_files_analyzed}")
                logger.info(f"Strategies Used: {summary.extraction_strategies_used}")
                logger.info(f"LLM Costs (USD): ${signal_report.cost_breakdown.total_cost_usd:.4f}")
                
                # Update unified result for inspection
                with open(output_file, "r") as f:
                    combined = json.load(f)
                
                combined["signal_intelligence"] = signal_report.model_dump(mode="json")
                
                with open(output_file, "w") as f:
                    json.dump(combined, f, indent=2)
                
                logger.info(f"📄 Final pipeline report updated in '{output_file}'")
                
            except Exception as e:
                logger.error(f"❌ Phase 3 failed: {str(e)}")
                # We show the error but continue to allow inspection of Phase 1&2
        except Exception as e:
            logger.error(f"❌ Phase 2 failed: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full Pipeline Verification (Stack + Pattern)")
    parser.add_argument("--path", type=str, required=True, help="Real repository path to analyze")
    args = parser.parse_args()
    
    asyncio.run(run_pipeline(args.path))
