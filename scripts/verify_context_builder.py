import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.agents.context_builder.agent import ContextBuilderAgent
from app.models.db_models import Job, StackReport

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/codereborn")

async def verify():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create a job without user_id since it's not in the DB
        job = Job(repo_path=os.getcwd(), status="running", tier="standard")
        session.add(job)
        await session.flush()
        
        stack_report = StackReport(
            job_id=job.id,
            analysis_scope="backend",
            primary_language="Python",
            report_data={"primary_language": "Python", "frameworks": [{"name": "FastAPI"}]}
        )
        session.add(stack_report)
        await session.commit()

        print(f"Created Job {job.id}. Starting ContextBuilderAgent...")
        agent = ContextBuilderAgent(session)
        try:
            context = await agent.execute(job.id, job.repo_path)
            print("\n--- CONTEXT BUILDER SUCCESS ---")
            print(f"Complexity Score: {context.complexity_score:.2f}")
            print(f"Files Ranked: {len(context.report_data.get('file_rankings', []))}")
            print(f"Samples Extracted: {len(context.report_data.get('architectural_samples', []))}")
        except Exception as e:
            print(f"Agent failed: {str(e)}")
            import traceback
            traceback.print_exc()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify())
