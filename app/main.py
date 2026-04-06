"""
FastAPI application factory for CodeReborn Engine.

Uses the lifespan pattern (replaces deprecated on_event) to manage
database and Redis connections across the app lifecycle.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.settings import get_settings
from app.mcp.server import mcp
from app.infrastructure.database import create_db_tables
from app.infrastructure.redis_client import close_redis_client, get_redis_client
from app.infrastructure.seeds import seed_initial_data

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup / shutdown lifecycle."""
    # Startup
    await create_db_tables()
    await seed_initial_data()
    await get_redis_client()   # warm up connection pool

    yield

    # Shutdown
    await close_redis_client()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Intelligence engine for legacy repositories analysis",
        version=settings.VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # ── MCP (Model Context Protocol) ──────────────────────────────────────
    # Expose tools to the frontend via SSE on /mcp/sse
    mcp_app = mcp.sse_app()
    app.mount("/mcp", mcp_app)

    # ── Health / meta endpoints ───────────────────────────────────────────
    @app.get("/health", tags=["Meta"], summary="Liveness probe")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": settings.VERSION})

    @app.get("/", tags=["Meta"], include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            {
                "service": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "docs": "/api/docs",
            }
        )

    return app


app = create_app()
