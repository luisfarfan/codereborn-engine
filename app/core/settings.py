from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "CodeReborn Engine"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Intelligence engine for legacy repositories analysis"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────────────────────────
    # Must use postgresql+asyncpg:// scheme for async driver
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codereborn"

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── LLM providers ────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # ── LLM budget defaults ───────────────────────────────────────────────
    LLM_DEFAULT_BUDGET_USD: float = 0.50
    LLM_MAX_BUDGET_USD: float = 5.00
    LLM_PREFERRED_MODEL: str = "gpt-4o-mini"

    # ── Auth ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # ── Observability ─────────────────────────────────────────────────────
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the postgresql+asyncpg:// scheme. "
                "Example: postgresql+asyncpg://user:pass@localhost:5432/db"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
