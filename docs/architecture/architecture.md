# 10. System Architecture

CodeReborn se diseña como una arquitectura distribuida basada en Controladores-Workers asíncronos y Event-Driven Analytics. Sigue los principios de **Clean Architecture + DDD** en su core para desacoplar el Framework del Dominio de Inteligencia.

**Componentes y Distribución Lógica:**

1.  **Capa Presentación / API (Repo Intelligence Interface):**
    *   FastAPI expone rutados síncronos HTTP. Bloquea peticiones excedentes mediante un Rate Limiter Redis (`100 rpm/job`).
    *   Interroga directamente la base de datos para recuperar artefactos, o lanza sub-agentes síncronos (`LiteLLM`) autorizados para contextos.
2.  **Capa Core Application (Job Engine):**
    *   Ingiere peticiones de análisis, las persiste y emite el encolamiento.
    *   Encapsula el `LLMBudgetService` (Gatekeeper).
3.  **Capa Autonomous Analytics (Workers / Orquestación):**
    *   Orquestal central gobernada por CrewAI. Dispara 5 Agentes Especializados de análisis y 4 Agentes Documentadores bajo grafos dirigidos dependientes.
4.  **Capa de Infraestructura (Persistencia, Eventos & Análisis):**
    *   `PostgreSQL`: Repositorio Central de Verdad. Todas las interacciones, heurísticas, AST metadata, métricas.
    *   `Deterministic Scanners`: Cli Binarios (Pylint, golangci-lint, specfy).
    *   `Redis`: Cola para workers y sistema inter-trabajos (PubSub).
    *   `[GAP INFERENCE] ChromaDB / PgVector`: Capa de embeddings rápida.

---

# 11. Data Architecture

PostgreSQL manejará tablas altamente relacionales fusionadas con columnas `JSONB` robustas (esencial para almacenar metadatos agnósticos de componentes variados como heurísticas y métricas externas de lenguajes heterogéneos).

**Esquema Relacional Extendido:**

*   `jobs`: PK `id` uuid. `repo_url`, `analysis_scope`, `budget_config` JSONB.
*   `llm_call_decisions`: Registro transaccional de resoluciones de `LLMBudgetService`. PK `id`, FK `job_id`.
*   `agent_executions`: Trazabilidad estricta obligatoria. FK `job_id`. *Tokens_used*, *cost_usd*, *model_used*, payload in/out JSONB.
*   `stack_reports`: FK `job_id`. Dependencias, servicios, infra hints detectados (JSONB).
*   `architecture_contexts`: FK `job_id`. Ranking y directorios.
*   `system_maps`: Arch report resultante de LLM. FK `job_id`.
*   `tech_debt_findings`: FK `job_id`. Individual rows para cada alerta del Linter y sus issues.
*   `tech_debt_analyses`: Conclusión consolidada post Fase 2 LLM cruzando los findings con el mapa.
*   `doc_artifacts`: `doc_type` enum (technical | human | ai_context | debt), `format` (markdown | json), `content` (TEXT), FK `job_id`.

*[RECOMMENDATION]: Construcción de Índices `GIN` sobre las columnas `JSONB` críticas (ej. `doc_artifacts.content` o `system_maps.components_identified`) para habilitar búsquedas determinísticas rápidas en el API.*
