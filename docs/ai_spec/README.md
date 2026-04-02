# AI Spec — Machine-Readable JSON Specs

These JSON files are structured specifically for AI agents and IDE assistants to consume as precise, factual context about the CodeReborn Engine system.

## When to use these files

Use these instead of (or alongside) the Markdown docs when you need **precise, structured facts** without prose — ideal for agent context windows and IDE AI features.

## Files

| File | Contents |
|------|----------|
| [index.json](index.json) | **Start here.** One-page system summary: vision, stack, all 7 components, critical rules, open gaps |
| [01_core_architecture.json](01_core_architecture.json) | Architecture facts, extension points, patterns, anti-patterns, constraints |
| [02_database_schema.json](02_database_schema.json) | All database tables, relationships, and schema rules |
| [03_pipeline_agents.json](03_pipeline_agents.json) | Pipeline execution order, per-agent facts and rules |
| [04_repo_intelligence_api.json](04_repo_intelligence_api.json) | REST API — 6 domains, endpoints, auth, rate limits (high-level) |
| [05_data_contracts.json](05_data_contracts.json) | **Formal schemas** for every data structure produced/consumed by the pipeline (generate Pydantic models from this) |
| [06_api_contracts.json](06_api_contracts.json) | **Complete API contracts** — every endpoint with request/response schemas (generate FastAPI routes from this) |
| [07_implementation_map.json](07_implementation_map.json) | **Spec → code mapping** — expected Python file paths, class names, and models for every component |

## Reading order for new agents

1. `index.json` — system overview (2 min)
2. `01_core_architecture.json` — layers, boundaries, and non-negotiable rules
3. `03_pipeline_agents.json` — what runs, in what order, and why
4. `07_implementation_map.json` — where every component lives in the codebase
5. `05_data_contracts.json` — exact shapes of all data structures
6. `02_database_schema.json` — persistence layer
7. `06_api_contracts.json` — REST API surface (only if working on the API)
