import asyncio
import uuid
import logging
import argparse
from sqlmodel import select
from app.infrastructure.database import AsyncSessionFactory
from app.models.db_models import Job, StackReport
from app.agents.pattern_detector.agent import PatternDetectorAgent
from app.domain.enums import AnalysisScope

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_pattern_detector(repo_path: str):
    """
    Verification script for the new Pattern Detector Agent.
    Requires a job and a stack report to exist in the DB.
    """
    async with AsyncSessionFactory() as session:
        # 1. Create a dummy job if none provided (or use existing)
        job_id = uuid.uuid4()
        job = Job(
            id=job_id,
            repo_path=repo_path,
            status="pending",
            analysis_scope=AnalysisScope.ALL
        )
        session.add(job)
        
        # 2. Add a minimal StackReport to mock prerequisite
        # In a real scenario, StackDetectorAgent would have run first
        mock_report_data = {
            "project_name": "VerifyProject",
            "primary_language": "python",
            "analysis_scope": "all",
            "languages": [{"language": "python", "estimated_percentage": 100.0}],
            "frameworks": [{"name": "fastapi", "category": "web_framework", "confidence_score": 1.0}],
            "file_inventory": {
                "total_files": 10,
                "by_type": {"code": 5, "tests": 2, "configs": 3}
            },
            "directory_structure": {
                "root_directories": [
                    {"path": "app", "name": "app", "depth": 1, "subdirectories": ["api", "models"], "file_count": 5, "file_breakdown": {"python": 5}, "total_lines": 500},
                    {"path": "tests", "name": "tests", "depth": 1, "subdirectories": [], "file_count": 2, "file_breakdown": {"python": 2}, "total_lines": 100}
                ]
            }
        }
        
        stack_report = StackReport(
            job_id=job_id,
            report_data=mock_report_data,
            primary_language="python"
        )
        session.add(stack_report)
        await session.commit()
        
        logger.info(f"Created dummy job {job_id} and stack report for verification.")

        # 3. Execute Pattern Detector
        agent = PatternDetectorAgent(session)
        logger.info(f"Executing PatternDetectorAgent for path: {repo_path}")
        
        try:
            report = await agent.execute(job_id, repo_path)
            logger.info("Pattern Detector execution successful!")
            logger.info(f"Primary Pattern detected: {report.detected_patterns.primary_pattern}")
            logger.info(f"Confidence: {report.detected_patterns.confidence}")
            logger.info(f"Recommended sampling: {report.sampling_strategy.recommended_sample_size} files")
            
            # Print directory interpretations
            for path, interpretation in report.directory_interpretation.items():
                logger.info(f"Directory [{path}]: {interpretation.purpose} ({interpretation.architectural_role})")
                
        except Exception as e:
            logger.error(f"Pattern Detector verification failed: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Pattern Detector Agent")
    parser.get_argument("--path", type=str, required=True, help="Path to analyze")
    args = parser.parse_args()
    
    asyncio.run(verify_pattern_detector(args.path))
