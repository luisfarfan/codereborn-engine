"""
FastAPI shared dependencies.

All route handlers obtain infrastructure resources through these functions
via Depends(), keeping the routes thin and easily testable via overrides.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings, get_settings
from app.infrastructure.database import get_session
from app.infrastructure.redis_client import get_redis
from app.services.llm_budget_service import LLMBudgetService


# ── Re-export infrastructure deps ────────────────────────────────────────────

async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncGenerator[AsyncSession, None]:
    yield session


async def get_cache(redis: Redis = Depends(get_redis)) -> AsyncGenerator[Redis, None]:
    yield redis


# ── Service deps ─────────────────────────────────────────────────────────────

def get_llm_budget_service(
    settings: Settings = Depends(get_settings),
) -> LLMBudgetService:
    return LLMBudgetService(
        default_budget_usd=settings.LLM_DEFAULT_BUDGET_USD,
        max_budget_usd=settings.LLM_MAX_BUDGET_USD,
    )
