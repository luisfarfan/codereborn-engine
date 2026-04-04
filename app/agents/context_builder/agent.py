import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.context_builder.crawler import RepoCrawler
from app.agents.context_builder.extractor import SignalExtractor
from app.agents.context_builder.inductor import ArchitecturalInductor
from app.agents.context_builder.classifier import DynamicClassifier
from app.agents.context_builder.ranker import ArchitecturalRanker
from app.agents.context_builder.sampler import ArchitecturalSampler
from app.domain.enums import AgentName, AgentStatus
from app.models.db_models import AgentExecution, ArchitectureContext, StackReport
from app.services.notification_service import NotificationService
from app.services.llm_budget_service import LLMBudgetService

logger = logging.getLogger(__name__)

class ContextBuilderAgent:
    """
    Agent responsible for building the Architecture Context Payload.
    Hybrid approach: Deterministic Signal Extraction + Cheap LLM Induction.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        # Initialize budget service (in-memory state managed per job)
        self.budget_service = LLMBudgetService()

    async def execute(self, job_id: uuid.UUID, repo_path: str) -> ArchitectureContext:
        """
        Runs the full universal context building pipeline.
        """
        # 1. Initialize AgentExecution
        execution = await self._get_or_create_execution(job_id)
        
        # Open budget for this job if not already open
        self.budget_service.open_job(str(job_id))
        
        await NotificationService.notify_agent_started(
            job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, "Building Universal Architecture Context"
        )

        try:
            root_path = Path(repo_path).resolve()
            
            # 2. CRAWL (20%)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, 20, "Crawling repository tree..."
            )
            crawler = RepoCrawler(repo_path)
            crawl_data = crawler.crawl()
            files = crawl_data["files"]
            
            # 3. EXTRACT DNA (40%)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, 40, "Extracting technical DNA signals..."
            )
            extractor = SignalExtractor(repo_path)
            dna_snapshot = extractor.get_dna_snapshot(files)
            
            # 4. INDUCE RULES (60%)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, 60, "Inducing architectural patterns (LLM-assisted)..."
            )
            stack_report_data = await self._get_stack_report_data(job_id)
            inductor = ArchitecturalInductor(self.budget_service)
            induced_schema = await inductor.induce(
                str(job_id), 
                dna_snapshot, 
                crawl_data["directory_summaries"],
                stack_report_data
            )
            
            # 5. CLASSIFY (70%)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, 70, "Classifying files with induced rules..."
            )
            classifier = DynamicClassifier(induced_schema)
            
            classifications = {}
            zones = {}
            # Cache file signals for classification performance
            for f in files:
                f_signals = extractor.extract_from_file(root_path / f)
                cls = classifier.classify(f, f_signals)
                classifications[str(f)] = cls
                
                # Assign to functional zones (simple strategy: by root folder or zone rules)
                zone_name = f.parts[0] if len(f.parts) > 1 else "root"
                if zone_name not in zones:
                    zones[zone_name] = {"zone_name": zone_name, "description": f"Zone: {zone_name}", "files": []}
                zones[zone_name]["files"].append(str(f))

            # 6. RANK (80%)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, 80, "Ranking high-value files (Fan-in/out)..."
            )
            ranker = ArchitecturalRanker(root_path)
            ranker.analyze_dependencies(files)
            ranker.calculate_scores(files, classifications)
            rankings = ranker.get_rankings()
            
            # 7. SAMPLE (100%)
            await NotificationService.notify_agent_progress(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, 95, "Extracting architectural samples..."
            )
            sampler = ArchitecturalSampler(root_path)
            top_ranked = [r["file_path"] for r in rankings[:15]] 
            
            samples = []
            for fp_str in top_ranked:
                fp = Path(fp_str)
                role = classifications.get(fp_str, {}).get("role", "unknown")
                zone = fp.parts[0] if len(fp.parts) > 1 else "root"
                samples.append(sampler.sample(fp, role, zone))

            # 8. ASSEMBLE PAYLOAD
            payload = {
              "repo_tree_summary": crawl_data["directory_summaries"],
              "zones": list(zones.values()),
              "induced_rules": induced_schema, # Save for debug/trace
              "file_classifications": classifications,
              "file_rankings": rankings,
              "architectural_samples": samples,
              "selection_rationale": "Top ranked by Fan-in/out and structural importance.",
              "directory_purposes": {z["zone_name"]: z["description"] for z in zones.values()},
              "estimated_context_size_tokens": int(crawl_data["total_size_bytes"] / 4),
              "metadata": {
                  "timestamp": datetime.utcnow().isoformat(),
                  "builder_version": "2.0.0 (Universal)"
              }
            }

            # 9. PERSIST
            context_model = ArchitectureContext(
                job_id=job_id,
                report_data=payload,
                complexity_score=sum(r["value_score"] for r in rankings) / len(rankings) if rankings else 0.0,
                estimated_context_size_tokens=payload["estimated_context_size_tokens"]
            )
            
            q = select(ArchitectureContext).where(ArchitectureContext.job_id == job_id)
            existing_result = await self.session.execute(q)
            existing = existing_result.scalars().first()
            
            if existing:
                for key, value in context_model.model_dump(exclude={"id", "created_at"}).items():
                    setattr(existing, key, value)
                context_model = existing
            else:
                self.session.add(context_model)

            # Mark execution as completed
            execution.status = AgentStatus.SUCCESS.value
            execution.completed_at = datetime.utcnow()
            execution.output_type = "architecture_context"
            execution.output_summary = (
                f"Induced architecture: {len(induced_schema.get('framework_conventions', []))} patterns found. "
                f"Mapped {len(files)} files into {len(zones)} zones."
            )
            
            await NotificationService.notify_agent_completed(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, "completed", execution.output_summary
            )

            await self.session.commit()
            return context_model

        except Exception as e:
            logger.exception(f"ContextBuilderAgent failed for job {job_id}")
            execution.status = AgentStatus.FAILED.value
            execution.error_detail = str(e)
            execution.completed_at = datetime.utcnow()
            await NotificationService.notify_agent_completed(
                job_id, AgentName.ARCHITECTURE_CONTEXT_BUILDER, "failed", str(e)
            )
            await self.session.commit()
            raise

    async def _get_or_create_execution(self, job_id: uuid.UUID) -> AgentExecution:
        q = select(AgentExecution).where(
            AgentExecution.job_id == job_id,
            AgentExecution.agent_name == AgentName.ARCHITECTURE_CONTEXT_BUILDER
        )
        result = await self.session.execute(q)
        execution = result.scalars().first()
        
        if not execution:
            execution = AgentExecution(
                job_id=job_id,
                agent_name=AgentName.ARCHITECTURE_CONTEXT_BUILDER,
                status=AgentStatus.RUNNING.value,
                started_at=datetime.utcnow()
            )
            self.session.add(execution)
        else:
            execution.status = AgentStatus.RUNNING.value
            execution.started_at = datetime.utcnow()
        
        await self.session.flush()
        return execution

    async def _get_stack_report_data(self, job_id: uuid.UUID) -> Dict[str, Any] | None:
        q = select(StackReport).where(StackReport.job_id == job_id)
        result = await self.session.execute(q)
        report = result.scalars().first()
        return report.report_data if report else None
