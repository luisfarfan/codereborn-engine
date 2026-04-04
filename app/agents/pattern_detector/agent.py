import logging
import uuid
from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.pattern_detector.interpreter import PatternInterpreter
from app.domain.enums import AgentName, AgentStatus
from app.models.db_models import AgentExecution, ArchitectureContext, StackReport
from app.models.stack_models import PatternReport
from app.services.llm_budget_service import LLMBudgetService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class PatternDetectorAgent:
    """
    Agent responsible for interpreting repository structure into architectural patterns.
    Successor to ArchitectureContextBuilder. 
    Focuses on structural interpretation using LLM, not code extraction.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.budget_service = LLMBudgetService()
        self.interpreter = PatternInterpreter()

    async def execute(self, job_id: uuid.UUID, repo_path: str) -> PatternReport:
        """
        Runs the pattern detection pipeline.
        """
        # 1. Initialize AgentExecution
        execution = await self._get_or_create_execution(job_id)
        
        # Open budget (singleton service or managed per job)
        self.budget_service.open_job(str(job_id))
        
        await NotificationService.notify_agent_started(
            job_id, AgentName.PATTERN_DETECTOR, "Interpreting Architectural Patterns"
        )

        try:
            # 2. Get Stack Report (Prerequisite)
            stack_report = await self._get_stack_report(job_id)
            if not stack_report:
                raise ValueError(
                    f"StackReport not found for job {job_id}. "
                    "PatternDetector requires it."
                )

            # 3. Interpret Patterns (LLM Call)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.PATTERN_DETECTOR, 50, 
                "Analyzing directory structure with LLM..."
            )
            
            # The interpreter handles the LLM logic and budget checking internally
            report = await self.interpreter.interpret(
                str(job_id),
                stack_report,
                self.budget_service
            )

            # 4. Persist result in architecture_contexts table
            context_model = ArchitectureContext(
                job_id=job_id,
                report_data=report.model_dump(),
                complexity_score=report.confidence_score,
                estimated_context_size_tokens=(
                    report.sampling_strategy.recommended_sample_size * 500
                )
            )
            
            # Check for existing
            q = select(ArchitectureContext).where(
                ArchitectureContext.job_id == job_id
            )
            existing_result = await self.session.execute(q)
            existing = existing_result.scalars().first()
            
            if existing:
                for key, value in context_model.model_dump(
                    exclude={"id", "created_at"}
                ).items():
                    setattr(existing, key, value)
            else:
                self.session.add(context_model)

            # 5. Finalize Execution
            execution.status = AgentStatus.COMPLETED.value
            execution.completed_at = datetime.utcnow()
            execution.output_type = "pattern_report"
            execution.output_summary = (
                f"Detected {report.detected_patterns.primary_pattern} architecture "
                f"({report.detected_patterns.confidence*100:.0f}% confidence). "
                f"Recommended sampling {report.sampling_strategy.recommended_sample_size} files."
            )
            
            await NotificationService.notify_agent_completed(
                job_id, AgentName.PATTERN_DETECTOR, "completed", 
                execution.output_summary
            )

            await self.session.commit()
            return report

        except Exception as e:
            logger.exception(f"PatternDetectorAgent failed for job {job_id}")
            execution.status = AgentStatus.FAILED.value
            execution.error_detail = str(e)
            execution.completed_at = datetime.utcnow()
            await NotificationService.notify_agent_completed(
                job_id, AgentName.PATTERN_DETECTOR, "failed", str(e)
            )
            await self.session.commit()
            raise

    async def _get_or_create_execution(self, job_id: uuid.UUID) -> AgentExecution:
        q = select(AgentExecution).where(
            AgentExecution.job_id == job_id,
            AgentExecution.agent_name == AgentName.PATTERN_DETECTOR
        )
        result = await self.session.execute(q)
        execution = result.scalars().first()
        
        if not execution:
            execution = AgentExecution(
                job_id=job_id,
                agent_name=AgentName.PATTERN_DETECTOR,
                status=AgentStatus.RUNNING.value,
                started_at=datetime.utcnow()
            )
            self.session.add(execution)
        else:
            execution.status = AgentStatus.RUNNING.value
            execution.started_at = datetime.utcnow()
        
        await self.session.flush()
        return execution

    async def _get_stack_report(self, job_id: uuid.UUID) -> StackReport | None:
        q = select(StackReport).where(StackReport.job_id == job_id)
        result = await self.session.execute(q)
        return result.scalars().first()
