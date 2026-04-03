import json
import uuid
from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.stack_detector.post_processor import StackPostProcessor
from app.agents.stack_detector.specfy_tool import SpecfyTool
from app.domain.enums import AgentName, AgentStatus
from app.models.db_models import AgentExecution, StackReport


class StackDetectorAgent:
    """
    Agent responsible for identified the core stack of a repository.
    Deterministic, high-fidelity engine.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tool = SpecfyTool()
        self.post_processor = StackPostProcessor()

    async def execute(self, job_id: uuid.UUID, repo_path: str) -> StackReport:
        """
        Runs the full detection pipeline for a specific job and persists results.
        """
        # 1. Initialize or find AgentExecution record
        execution = await self._start_execution(job_id)

        try:
            # 2. Raw Extraction using SpecfyTool
            raw_json = self.tool._run(repo_path)
            if raw_json.startswith("Error") or raw_json.startswith("Exception"):
                raise Exception(f"SpecfyTool failure: {raw_json}")

            # 3. Intelligent Post-Processing
            report = self.post_processor.process(raw_json, repo_path)

            # 4. Persistence into StackReport table
            stack_report_model = StackReport(
                job_id=job_id,
                analysis_scope=report.analysis_scope.value,
                primary_language=report.primary_language,
                confidence_score=report.confidence_score,
                report_data=report.model_dump(mode="json"),
                raw_tool_output=self._parse_raw(raw_json)
            )

            # Upsert behavior if already exists (shouldn't happen on fresh jobs)
            existing_q = select(StackReport).where(StackReport.job_id == job_id)
            existing_result = await self.session.execute(existing_q)
            existing = existing_result.scalars().first()

            if existing:
                update_data = stack_report_model.model_dump(
                    mode="json", exclude={"id", "created_at"}
                )
                for key, value in update_data.items():
                    setattr(existing, key, value)
                stack_report_model = existing
            else:
                self.session.add(stack_report_model)

            # 5. Mark execution as completed
            await self._complete_execution(execution)

            await self.session.commit()
            return stack_report_model

        except Exception as e:
            await self._fail_execution(execution, str(e))
            await self.session.commit()
            raise

    async def _start_execution(self, job_id: uuid.UUID) -> AgentExecution:
        # Check if already exists for this job and agent
        q = select(AgentExecution).where(
            AgentExecution.job_id == job_id,
            AgentExecution.agent_name == AgentName.STACK_DETECTOR
        )
        result = await self.session.execute(q)
        execution = result.scalars().first()

        if not execution:
            execution = AgentExecution(
                job_id=job_id,
                agent_name=AgentName.STACK_DETECTOR,
                status=AgentStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            self.session.add(execution)
        else:
            execution.status = AgentStatus.RUNNING
            execution.started_at = datetime.utcnow()
            execution.error_detail = None

        return execution

    async def _complete_execution(self, execution: AgentExecution):
        execution.status = AgentStatus.COMPLETED
        execution.completed_at = datetime.utcnow()

    async def _fail_execution(self, execution: AgentExecution, error: str):
        execution.status = AgentStatus.FAILED
        execution.error_detail = error
        execution.completed_at = datetime.utcnow()

    def _parse_raw(self, raw_json: str) -> dict:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return {"raw_str": raw_json}
