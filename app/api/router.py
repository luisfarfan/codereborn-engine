"""
API v1 root router.

All domain routers are registered here and then mounted onto the FastAPI app
with the /api/v1 prefix. Adding a new domain = one import + one include_router.
"""

from fastapi import APIRouter

from app.api.routers import (
    agents,
    auth,
    docs,
    impact,
    jobs,
    navigation,
    stream,
    task_context,
    understanding,
)

api_router = APIRouter()

# Core job lifecycle + frontend-facing endpoints
api_router.include_router(auth.router)         # GET /auth/me (Mock)
api_router.include_router(jobs.router)
api_router.include_router(stream.router)       # GET /jobs/{id}/stream (SSE)
api_router.include_router(agents.router)       # GET /agents (static catalog)

# Repo Intelligence Interface (MCP-style read endpoints)
api_router.include_router(understanding.router)
api_router.include_router(navigation.router)
api_router.include_router(task_context.router)
api_router.include_router(impact.router)
api_router.include_router(docs.router)
