---
inclusion: always
---

# CodeReborn Engine

Intelligence engine that transforms legacy repositories into structured knowledge via a deterministic + LLM hybrid pipeline (CrewAI agents) exposed through a FastAPI REST API.

**Stack:** Python 3.11+ · FastAPI · CrewAI · PostgreSQL 15 · Redis 7 · LiteLLM · Langfuse  
**Architecture:** Hexagonal · Async AI Worker Clusters

## Documentation Index

- Full index: `docs/README.md`
- Machine-readable summary: `docs/ai_spec/index.json`
- Master spec: `PROMPT.AI`

## Pipeline (order)

1. **StackDetector** (deterministic — specfy CLI)
2. **ContextBuilder** (deterministic — graph-based tree scorer)
3. **SystemMapper** (LLM — CrewAI, budget-gated)
4. **TechDebtAnalyzer** (hybrid — linters + LLM)
5. **DocWritingLayer** (4 parallel LLM agents)
6. **IntelligenceInterface** (FastAPI REST)

## Non-Negotiable Rules

- No LLM in StackDetector or ContextBuilder — they are fully deterministic
- Every LLM call needs clearance from `LLMBudgetService` first
- Redis = rate-limiting + PubSub only (not pipeline data)
- All agent data exchange through PostgreSQL

## Out of Scope — DO NOT generate

- **Tests are explicitly out of scope.** Do not create, suggest, or modify any files under `tests/`. Do not add test cases, pytest fixtures, or testing utilities unless the user explicitly asks for it.

## Code Locations

- `app/agents/` — agent implementations
- `app/services/` — LLMBudgetService and shared services
- `app/api/` — FastAPI routes
- `app/core/` — domain logic (framework-free)
- `app/infrastructure/` — DB, Redis, external integrations
