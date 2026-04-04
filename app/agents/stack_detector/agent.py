"""
Stack Detector Agent — Local repository scanner.

Identifies languages, frameworks, and services with high fidelity using
the Specfy stack-analyser engine and a deep deterministic repo scanner.
100% deterministic, no LLM cost.
"""

import json
import uuid
import logging
from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.stack_detector.post_processor import StackPostProcessor
from app.agents.stack_detector.specfy_tool import SpecfyTool
from app.agents.stack_detector.scanner import RepoScanner
from app.domain.enums import AgentName, AgentStatus
from app.models.db_models import AgentExecution, StackReport
from app.services.notification_service import NotificationService


class StackDetectorAgent:
    """
    Agent responsible for identifying the core stack and structure of a repository.
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

        # 1.1 Notify Frontend
        await NotificationService.notify_agent_started(
            job_id, AgentName.STACK_DETECTOR, "Stack Detector v2.0"
        )

        try:
            # 2. Raw Extraction using SpecfyTool
            await NotificationService.notify_agent_progress(
                job_id, AgentName.STACK_DETECTOR, 10, "Running raw stack extraction (Specfy)..."
            )
            raw_json = self.tool._run(repo_path)
            if raw_json.startswith("Error") or raw_json.startswith("Exception"):
                # Graceful degradation if specfy fails, we still want the scanner
                logger.warning(f"SpecfyTool failed for {job_id}: {raw_json}")
                raw_json = "{}" 

            # 3. Intelligent Post-Processing (Phase 1)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.STACK_DETECTOR, 40, "Refining stack intelligence..."
            )
            report = self.post_processor.process(raw_json, repo_path)

            # 4. Deep Filesystem Scan (Phase 2 - NEW)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.STACK_DETECTOR, 60, "Generating File Inventory & Directory Structure..."
            )
            scanner = RepoScanner(repo_path, report.analysis_scope)
            scan_results = scanner.scan()
            
            # Merge results into report
            report.file_inventory = scan_results["file_inventory"]
            report.directory_structure = scan_results["directory_structure"]
            report.repository_metadata = scan_results["repository_metadata"]

            # 5. Persistence into StackReport table
            stack_report_model = StackReport(
                job_id=job_id,
                analysis_scope=report.analysis_scope.value,
                primary_language=report.primary_language,
                confidence_score=report.confidence_score,
                report_data=report.model_dump(mode="json"),
                raw_tool_output=self._parse_raw(raw_json)
            )

            # Upsert behavior if already exists
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

            # Update AgentExecution with output summary
            summary = (
                f"Detected {report.primary_language}. "
                f"Inventoried {report.file_inventory.total_files} files "
                f"across {report.directory_structure.statistics['total_directories']} directories."
            )
            execution.output_type = "stack_report"
            execution.output_summary = summary

            # 6. Mark execution as completed
            await self._complete_execution(execution)
            await NotificationService.notify_agent_completed(
                job_id, AgentName.STACK_DETECTOR, "completed", summary
            )

            await self.session.commit()
            return stack_report_model

        except Exception as e:
            await self._fail_execution(execution, str(e))
            await NotificationService.notify_agent_completed(
                job_id, AgentName.STACK_DETECTOR, "failed", str(e)
            )
            await self.session.commit()
            raise

    async def _start_execution(self, job_id: uuid.UUID) -> AgentExecution:
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
                status=AgentStatus.RUNNING.value,
                started_at=datetime.utcnow()
            )
            self.session.add(execution)
        else:
            execution.status = AgentStatus.RUNNING.value
            execution.started_at = datetime.utcnow()
            execution.error_detail = None

        await self.session.flush()
        return execution

    async def _complete_execution(self, execution: AgentExecution):
        execution.status = AgentStatus.COMPLETED.value
        execution.completed_at = datetime.utcnow()

    async def _fail_execution(self, execution: AgentExecution, error: str):
        execution.status = AgentStatus.FAILED.value
        execution.error_detail = error
        execution.completed_at = datetime.utcnow()

    def _parse_raw(self, raw_json: str) -> dict:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return {"raw_str": raw_json}
