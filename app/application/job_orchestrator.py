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
from app.models.db_models import Job
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

                # 3. RUN Phase 2: Context Builder (Deterministic & Mapping)
                logger.info(f"Executing ContextBuilder for job {job_id}")
                from app.agents.context_builder.agent import ContextBuilderAgent
                context_builder = ContextBuilderAgent(session)

                try:
                    await context_builder.execute(job_id, target_path)
                except Exception as e:
                    logger.error(f"ContextBuilder failed: {str(e)}")
                    # ContextBuilder failure is critical as it feeds LLM agents
                    await self._fail_job(session, job, f"Context Building failed: {str(e)}")
                    return

                # 4. RUN Phase 3: System Mapper & Beyond (To be integrated)

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
