# CodeReborn Engine — AI Agent Guide

> Universal entry point for AI coding assistants (Cursor, Claude Code, Kiro, GitHub Copilot, etc.)

## Quick Summary

CodeReborn Engine analyzes legacy repositories and transforms them into structured intelligence. It runs a **deterministic + LLM hybrid pipeline** using CrewAI agents, stores results in PostgreSQL, and exposes everything via a FastAPI REST API.

**Stack:** Python 3.11+ · FastAPI · CrewAI · PostgreSQL 15 · Redis 7 · LiteLLM · Langfuse  
**Architecture:** Clean Architecture + DDD · Async AI Worker Clusters

---

## Documentation

| Resource | Purpose |
|----------|---------|
| [`docs/README.md`](docs/README.md) | Full documentation index — start here |
| [`docs/ai_spec/index.json`](docs/ai_spec/index.json) | Machine-readable system summary (best for agent context) |
| [`PROMPT.AI`](PROMPT.AI) | Master specification (~1400 lines, comprehensive) |

### Docs by topic
- **Vision & stack** → `docs/overview/`
- **Domain model & requirements** → `docs/domain/`
- **Architecture & DB** → `docs/architecture/`
- **Pipeline flow** → `docs/pipeline/`
- **Each agent's spec** → `docs/agents/`
- **REST API** → `docs/api/`
- **LLM budgeting & ops** → `docs/operations/`
- **Open gaps** → `docs/roadmap/`

---

## Critical Rules

1. `StackDetector` and `ContextBuilder` are **100% deterministic — no LLM calls**.
2. Every LLM call requires **prior clearance from `LLMBudgetService`** (`app/services/`).
3. Redis is **only** for rate-limiting and PubSub notifications — never pipeline data.
4. All agent-to-agent data flows through **PostgreSQL** (CrewAI shared context + JSONB).

## Out of Scope — DO NOT generate

- **Tests are explicitly out of scope.** Do not create, suggest, or modify any files under `tests/`. Do not add test cases, pytest fixtures, or testing utilities unless the user explicitly asks for it.

---

## App Structure

```
app/
├── agents/          context_builder · debt_analyzer · doc_writers · stack_detector · system_mapper
├── api/             FastAPI route handlers
├── application/     Use cases / application services
├── core/            Domain logic (pure, no framework dependencies)
├── domain/          Domain models and value objects
├── infrastructure/  DB (SQLModel/asyncpg), Redis, external services
├── models/          SQLModel ORM models
└── services/        Shared services — LLMBudgetService, etc.
```

---

## Local Setup

```bash
cp .env.example .env          # fill in secrets
docker compose up -d          # PostgreSQL 15 + Redis 7
pip install -e .              # installs via pyproject.toml
uvicorn app.main:app --reload # dev server
```
