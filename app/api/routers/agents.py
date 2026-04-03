"""
Agents catalog router — GET /agents.

Returns the static catalog of all available pipeline agents along with
the supported LLM models for each agent and the analysis tiers.

This endpoint is 100% static (no DB, no LLM). The catalog is defined
in code and only changes when agents are added or removed from the pipeline.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/agents", tags=["Agents"])


# ── Static Model Catalog ──────────────────────────────────────────────────────

_MODEL_GPT4_TURBO = {
    "id": "gpt-4-turbo",
    "name": "GPT-4 Turbo",
    "provider": "openai",
    "cost_per_1k_input": 0.01,
    "cost_per_1k_output": 0.03,
    "context_window": 128000,
    "specialty": "Balanced performance and accuracy",
    "recommended_for": ["general analysis", "standard codebases"],
}
_MODEL_GPT35 = {
    "id": "gpt-3.5-turbo",
    "name": "GPT-3.5 Turbo",
    "provider": "openai",
    "cost_per_1k_input": 0.0005,
    "cost_per_1k_output": 0.0015,
    "context_window": 16000,
    "specialty": "Cost-efficient for simple architectures",
    "recommended_for": ["budget-conscious", "simple codebases"],
}
_MODEL_CLAUDE_OPUS = {
    "id": "claude-opus-3.5",
    "name": "Claude Opus 3.5",
    "provider": "anthropic",
    "cost_per_1k_input": 0.015,
    "cost_per_1k_output": 0.075,
    "context_window": 200000,
    "specialty": "Deep architectural reasoning and pattern detection",
    "recommended_for": ["complex architectures", "large codebases"],
}
_MODEL_CLAUDE_HAIKU = {
    "id": "claude-haiku",
    "name": "Claude Haiku",
    "provider": "anthropic",
    "cost_per_1k_input": 0.00025,
    "cost_per_1k_output": 0.00125,
    "context_window": 200000,
    "specialty": "Fast and cost-effective analysis",
    "recommended_for": ["tech debt detection", "code quality"],
}
_MODEL_LLAMA = {
    "id": "llama-3-70b",
    "name": "Llama 3 70B",
    "provider": "meta",
    "cost_per_1k_input": 0.0,
    "cost_per_1k_output": 0.0,
    "context_window": 8000,
    "specialty": "Free open source model",
    "recommended_for": ["budget tier", "experimentation"],
}


# ── Agent Catalog ─────────────────────────────────────────────────────────────

_AGENTS_CATALOG = [
    {
        "id": "stack_detector",
        "name": "Stack Detector",
        "description": (
            "Detects technologies, frameworks, dependencies, and services "
            "used in the repository. 100% deterministic — no LLM calls."
        ),
        "order": 1,
        "uses_llm": False,
        "task_type": None,
        "default_model": None,
        "available_models": [],
        "required": True,
        "estimated_duration_seconds": 120,
    },
    {
        "id": "context_builder",
        "name": "Architecture Context Builder",
        "description": (
            "Builds curated architectural context for LLM analysis by "
            "crawling and classifying repository files. Deterministic."
        ),
        "order": 2,
        "uses_llm": False,
        "task_type": None,
        "default_model": None,
        "available_models": [],
        "required": True,
        "estimated_duration_seconds": 180,
    },
    {
        "id": "system_mapper",
        "name": "System Mapper",
        "description": "Maps the real architecture of the codebase using LLM analysis.",
        "order": 3,
        "uses_llm": True,
        "task_type": "analysis",
        "default_model": "gpt-4-turbo",
        "available_models": [
            _MODEL_CLAUDE_OPUS,
            _MODEL_GPT4_TURBO,
            _MODEL_GPT35,
            _MODEL_LLAMA,
        ],
        "required": True,
        "estimated_duration_seconds": 600,
    },
    {
        "id": "tech_debt_analyzer",
        "name": "Tech Debt Analyzer",
        "description": "Detects and prioritizes technical debt across the codebase.",
        "order": 4,
        "uses_llm": True,
        "task_type": "analysis",
        "default_model": "claude-haiku",
        "available_models": [_MODEL_CLAUDE_HAIKU, _MODEL_GPT35],
        "required": True,
        "estimated_duration_seconds": 300,
    },
    {
        "id": "technical_doc_writer",
        "name": "Technical Doc Writer",
        "description": "Generates technical documentation for developers.",
        "order": 5,
        "uses_llm": True,
        "task_type": "text_generation",
        "default_model": "gpt-3.5-turbo",
        "available_models": [_MODEL_GPT4_TURBO, _MODEL_GPT35],
        "required": False,
        "estimated_duration_seconds": 240,
    },
    {
        "id": "human_doc_writer",
        "name": "Human Doc Writer",
        "description": "Generates human-friendly onboarding documentation.",
        "order": 6,
        "uses_llm": True,
        "task_type": "text_generation",
        "default_model": "gpt-3.5-turbo",
        "available_models": [_MODEL_GPT35],
        "required": False,
        "estimated_duration_seconds": 180,
    },
    {
        "id": "ai_context_writer",
        "name": "AI Context Writer",
        "description": "Generates AI-friendly structured documentation.",
        "order": 7,
        "uses_llm": True,
        "task_type": "structured_generation",
        "default_model": "gpt-3.5-turbo",
        "available_models": [_MODEL_GPT35],
        "required": False,
        "estimated_duration_seconds": 120,
    },
    {
        "id": "debt_doc_writer",
        "name": "Debt Doc Writer",
        "description": "Generates technical debt documentation and recommendations.",
        "order": 8,
        "uses_llm": True,
        "task_type": "text_generation",
        "default_model": "claude-haiku",
        "available_models": [_MODEL_CLAUDE_HAIKU],
        "required": False,
        "estimated_duration_seconds": 150,
    },
]

_TIERS_CATALOG = [
    {
        "id": "budget",
        "name": "Budget",
        "description": "Uses free/cheap LLMs. Good for experimentation.",
        "default_models": {
            "system_mapper": "llama-3-70b",
            "tech_debt_analyzer": "gpt-3.5-turbo",
            "technical_doc_writer": "gpt-3.5-turbo",
            "human_doc_writer": "gpt-3.5-turbo",
            "ai_context_writer": "gpt-3.5-turbo",
            "debt_doc_writer": "gpt-3.5-turbo",
        },
        "estimated_cost_range": "0.00 - 1.00 USD",
    },
    {
        "id": "standard",
        "name": "Standard",
        "description": "Balanced performance and cost. Recommended for most projects.",
        "default_models": {
            "system_mapper": "gpt-4-turbo",
            "tech_debt_analyzer": "claude-haiku",
            "technical_doc_writer": "gpt-3.5-turbo",
            "human_doc_writer": "gpt-3.5-turbo",
            "ai_context_writer": "gpt-3.5-turbo",
            "debt_doc_writer": "claude-haiku",
        },
        "estimated_cost_range": "2.00 - 8.00 USD",
    },
    {
        "id": "premium",
        "name": "Premium",
        "description": "Best models for highest accuracy. For complex/critical projects.",
        "default_models": {
            "system_mapper": "claude-opus-3.5",
            "tech_debt_analyzer": "gpt-4-turbo",
            "technical_doc_writer": "gpt-4-turbo",
            "human_doc_writer": "gpt-4-turbo",
            "ai_context_writer": "gpt-4-turbo",
            "debt_doc_writer": "gpt-4-turbo",
        },
        "estimated_cost_range": "8.00 - 20.00 USD",
    },
]


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.get(
    "",
    summary="List available agents and analysis tiers",
    description=(
        "Returns the static catalog of all pipeline agents with their supported "
        "LLM models, and the available analysis tiers (budget/standard/premium) "
        "with their default model assignments."
    ),
)
async def list_agents() -> JSONResponse:
    return JSONResponse(
        content={
            "agents": _AGENTS_CATALOG,
            "tiers": _TIERS_CATALOG,
        }
    )
