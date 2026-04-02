# CodeReborn Engine — Documentation Index

> **For AI Agents & IDE Assistants:** Start with `ai_spec/index.json` for a machine-readable summary of the entire system. This README maps every document by topic.

## What is CodeReborn Engine?

An intelligence engine that transforms legacy repositories into structured, indexable knowledge. It runs a deterministic + LLM hybrid pipeline (via CrewAI) and exposes results through a FastAPI REST interface.

**Core Stack:** FastAPI · CrewAI · PostgreSQL · Redis · LiteLLM · Langfuse · specfy/stack-analyser

**Architectural style:** Clean Architecture + DDD · Event-Driven · Async AI Worker Clusters

---

## Folder Structure

```
docs/
├── overview/        ← Vision, principles, tech stack
├── domain/          ← Domain model, requirements, analysis modes
├── architecture/    ← System architecture, DB schema, orchestration
├── pipeline/        ← Pipeline flow and LLM budget service
├── agents/          ← Each agent's spec + orchestration
├── api/             ← REST API interfaces
├── operations/      ← LLM budgeting, ops, validation
├── roadmap/         ← Open gaps and next steps
└── ai_spec/         ← Machine-readable JSON specs (for AI agents)
```

---

## Documents by Topic

### Overview
| File | Description |
|------|-------------|
| [overview/principles_and_vision.md](overview/principles_and_vision.md) | Core philosophy: deterministic-first, LLM as last resort, "regla cero" |
| [overview/vision_and_scope.md](overview/vision_and_scope.md) | Executive overview, SDD pillars, V1 in/out of scope |
| [overview/technological_stack.md](overview/technological_stack.md) | Stack rationale: CrewAI, PostgreSQL, FastAPI, Redis, specfy |

### Domain & Requirements
| File | Description |
|------|-------------|
| [domain/requirements_and_rules.md](domain/requirements_and_rules.md) | Functional/non-functional requirements, business rules, main pipeline flow |
| [domain/domain_model.md](domain/domain_model.md) | Job context, economic context, code-representation context; actors |
| [domain/analysis_scope_and_modes.md](domain/analysis_scope_and_modes.md) | `single_pass` / `multi_zone` / `hierarchical_multi_zone` modes |

### Architecture
| File | Description |
|------|-------------|
| [architecture/architecture.md](architecture/architecture.md) | Clean Architecture layers, FastAPI + Job engine + CrewAI workers + infra |
| [architecture/database_schema.md](architecture/database_schema.md) | Tables: `jobs`, `llm_call_decisions`, `agent_executions`, reports, `doc_artifacts` |
| [architecture/orchestration_and_communication.md](architecture/orchestration_and_communication.md) | CrewAI shared context, task graph, Redis scope |

### Pipeline
| File | Description |
|------|-------------|
| [pipeline/pipeline_and_budget_service.md](pipeline/pipeline_and_budget_service.md) | Execution order, `LLMBudgetService` algorithm, `LLMCallDecision` JSON shape |

### Agents
| File | Description |
|------|-------------|
| [agents/stack_detector.md](agents/stack_detector.md) | Deterministic — specfy CLI wrapper, Stack Intelligence Report |
| [agents/context_builder.md](agents/context_builder.md) | Deterministic — graph-based tree crawler, zone ranking, `architecture_context_payload` |
| [agents/system_mapper.md](agents/system_mapper.md) | LLM — dominant architecture analysis, budget pre-check, System Map Report |
| [agents/tech_debt_analyzer.md](agents/tech_debt_analyzer.md) | Hybrid — Phase 1 linters, Phase 2 LLM synthesis, Tech Debt Report |
| [agents/doc_writing_layer.md](agents/doc_writing_layer.md) | LLM — 4 parallel writers (technical, human, AI JSON, debt), `doc_artifacts` |
| [agents/agents_orchestration.md](agents/agents_orchestration.md) | JobManager, task graph, parallel doc tasks, Redis PubSub notifications |

### API
| File | Description |
|------|-------------|
| [api/interfaces_and_api.md](api/interfaces_and_api.md) | API domains overview, RAG/PgVector recommendations |
| [api/repo_intelligence_interface.md](api/repo_intelligence_interface.md) | 6 REST domains, endpoints, auth (Bearer), rate limit (100 rpm/job) |

### Operations
| File | Description |
|------|-------------|
| [operations/llm_and_budgeting.md](operations/llm_and_budgeting.md) | LLM interception, gatekeeper logic, LiteLLM settlement, tier 1/2/3 strategy |
| [operations/operations.md](operations/operations.md) | Security, Langfuse observability, failure modes, testing, scalability |
| [operations/validation_and_quality.md](operations/validation_and_quality.md) | Tiered repo validation, quality metrics, philosophical principles |

### Roadmap
| File | Description |
|------|-------------|
| [roadmap/gaps_and_next_steps.md](roadmap/gaps_and_next_steps.md) | Open questions: PgVector vs Chroma, Celery/ARQ, MCP, sandbox retention |

### Machine-Readable Specs (AI agents)
| File | Description |
|------|-------------|
| [ai_spec/index.json](ai_spec/index.json) | One-page system summary: vision, stack, components, rules, gaps |
| [ai_spec/01_core_architecture.json](ai_spec/01_core_architecture.json) | Architecture facts, rules, boundaries, anti-patterns |
| [ai_spec/02_database_schema.json](ai_spec/02_database_schema.json) | DB schema facts and constraints |
| [ai_spec/03_pipeline_agents.json](ai_spec/03_pipeline_agents.json) | Pipeline/agent rules and facts |
| [ai_spec/04_repo_intelligence_api.json](ai_spec/04_repo_intelligence_api.json) | API domains, auth, rate limits (high-level) |
| [ai_spec/05_data_contracts.json](ai_spec/05_data_contracts.json) | **Formal schemas** for every agent output (Pydantic-ready) |
| [ai_spec/06_api_contracts.json](ai_spec/06_api_contracts.json) | **Complete API contracts** with request/response schemas per endpoint |
| [ai_spec/07_implementation_map.json](ai_spec/07_implementation_map.json) | **Spec → code** — Python file paths, class names, and models for every component |

---

## Critical Rules (for AI Agents)

1. **No LLM for deterministic work** — StackDetector and ContextBuilder never call LLMs.
2. **Every LLM call requires prior clearance** from `LLMBudgetService`.
3. **Strict layer separation** — extraction → correlation/mapping → documentation artifacts.

---

## Root Files

| File | Description |
|------|-------------|
| `PROMPT.AI` | Master system specification (comprehensive, ~1400 lines) |
| `pyproject.toml` | Python project config (FastAPI, CrewAI, SQLModel, Pydantic) |
| `docker-compose.yml` | Local infra: PostgreSQL 15 + Redis 7 |
| `.env.example` | Environment variables template |
