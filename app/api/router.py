"""
API v1 root router.

All domain routers are registered here and then mounted onto the FastAPI app
with the /api/v1 prefix. Adding a new domain = one import + one include_router.
"""

from fastapi import APIRouter

from app.api.routers import (
    docs,
    impact,
    jobs,
    navigation,
    task_context,
    understanding,
)

api_router = APIRouter()

api_router.include_router(jobs.router)
api_router.include_router(understanding.router)
api_router.include_router(navigation.router)
api_router.include_router(task_context.router)
api_router.include_router(impact.router)
api_router.include_router(docs.router)
