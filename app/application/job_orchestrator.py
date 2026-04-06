"""
Job Orchestrator — The engine's central conductor.

Manages the end-to-end execution flow of a Job, calling agents in sequence,
updating the DB, and notifying the frontend via SSE.

This runs in the background (FastAPI BackgroundTasks or a proper worker).
"""

import logging
import uuid
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.stack_detector.agent import StackDetectorAgent
from app.domain.enums import JobStatus
from app.infrastructure.database import AsyncSessionFactory
from app.models.db_models import Job, SignalReport
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class JobOrchestrator:
    """
    Orchestrates the pipeline execution for a single job.
    """

    async def run_job(self, job_id: uuid.UUID) -> None:
        """
        Main entry point for background job execution.
        """
        async with AsyncSessionFactory() as session:
            try:
                # 1. Start Job
                job = await self._initialize_job(session, job_id)
                if not job:
                    return

                logger.info(f"Starting job {job_id} for repo: {job.repo_url or job.repo_path}")
                await NotificationService.notify_job_status(job_id, JobStatus.RUNNING.value)

                # 2. RUN Phase 1: Stack Detector (Deterministic & Critical)
                logger.info(f"Executing StackDetector for job {job_id}")
                stack_detector = StackDetectorAgent(session)

                # Use repo_path if available (local), else repo_url
                target_path = job.repo_path or "."

                try:
                    report = await stack_detector.execute(job_id, target_path)

                    # Update job with detected scope for summary view
                    job.analysis_scope = report.analysis_scope
                    session.add(job)
                    await session.commit()
                except Exception as e:
                    logger.error(f"StackDetector failed: {str(e)}")
                    await self._fail_job(session, job, f"Stack Detection failed: {str(e)}")
                    return

                # 3. RUN Phase 2: Pattern Detector (LLM-based Interpretation)
                logger.info(f"Executing PatternDetector for job {job_id}")
                from app.agents.pattern_detector.agent import PatternDetectorAgent
                pattern_detector = PatternDetectorAgent(session)

                try:
                    pattern_report = await pattern_detector.execute(job_id, target_path)
                except Exception as e:
                    logger.error(f"PatternDetector failed: {str(e)}")
                    # PatternDetector failure is critical as it sets the sampling strategy
                    await self._fail_job(session, job, f"Pattern Detection failed: {str(e)}")
                    return

                # 4. RUN Phase 4: Universal Signal Extractor (Hybrid Extraction)
                logger.info(f"Executing UniversalExtractor for job {job_id}")
                from app.agents.universal_extractor.agent import UniversalExtractorAgent
                from app.services.llm_budget_service import LLMBudgetService
                
                extractor = UniversalExtractorAgent(LLMBudgetService())
                
                try:
                    # Execute extraction (sampling from pattern_report)
                    signal_report = await extractor.execute(
                        job_id=job_id,
                        repo_path=target_path,
                        stack_report=report,
                        pattern_report=pattern_report,
                        db_session=session
                    )
                    
                    # Persist SignalReport
                    from sqlmodel import select
                    q = select(SignalReport).where(SignalReport.job_id == job_id)
                    existing_result = await session.execute(q)
                    existing = existing_result.scalars().first()
                    
                    if existing:
                        existing.report_data = signal_report.model_dump(mode="json")
                        existing.analysis_timestamp = datetime.utcnow()
                        session.add(existing)
                    else:
                        db_report = SignalReport(
                            job_id=job_id,
                            report_data=signal_report.model_dump(mode="json")
                        )
                        session.add(db_report)
                    
                    await session.commit()
                except Exception as e:
                    logger.error(f"UniversalExtractor failed: {str(e)}")
                    # For MVP, we can continue if this fails, but better to fail if critical
                    await self._fail_job(session, job, f"Signal Extraction failed: {str(e)}")
                    return

                # 5. RUN Phase 5: System Mapper & Beyond

                # 4. Finalize Job
                await self._complete_job(session, job)
                logger.info(f"Job {job_id} completed successfully")

            except Exception as e:
                logger.exception(f"Unexpected error in JobOrchestrator for job {job_id}")
                # Try to mark as failed if possible
                try:
                    current_job = await session.get(Job, job_id)
                    if current_job:
                        err_msg = f"Internal Orchestrator Error: {str(e)}"
                        await self._fail_job(session, current_job, err_msg)
                except Exception as nested_e:
                    logger.error(f"Could not mark job as failed: {str(nested_e)}")

    async def _initialize_job(self, session: AsyncSession, job_id: uuid.UUID) -> Job | None:
        job = await session.get(Job, job_id)
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return None

        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    async def _complete_job(self, session: AsyncSession, job: Job) -> None:
        job.status = JobStatus.COMPLETED.value
        job.completed_at = datetime.utcnow()
        session.add(job)
        await session.commit()
        await NotificationService.notify_job_status(job.id, JobStatus.COMPLETED.value)
        await NotificationService.notify_job_completed(job.id, job.cost_usd)

    async def _fail_job(self, session: AsyncSession, job: Job, error: str) -> None:
        job.status = JobStatus.FAILED.value
        job.completed_at = datetime.utcnow()
        job.error_detail = error
        session.add(job)
        await session.commit()
        await NotificationService.notify_job_status(job.id, JobStatus.FAILED.value)
        await NotificationService.notify_job_failed(job.id, error)
