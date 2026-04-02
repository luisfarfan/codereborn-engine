# 04. Functional Requirements

*   **FR-001 [Budget Intercept]:** Toda ejecución LLM debe solicitar autorización al `LLMBudgetService` entregando una estimación pasiva de tokens.
*   **FR-002 [Fallback/Degradation]:** El sistema debe cambiar autónomamente el model o el analysis mode si el presupuesto de tokens/costo lo requiere, registrando un WARNING.
*   **FR-003 [Determinism First]:** La extracción inicial del stack debe usar wrappers del CLI determinístico `specfy/stack-analyser`.
*   **FR-004 [Architectural Ranking]:** El sistema debe valuar cada archivo basándose en import-graphs y centralidad arquitectónica (heurística), sin asumir limpiamente una arquitectura canónica.
*   **FR-005 [Hybrid Debt]:** Las deudas técnicas deben originarse primero por linters en subprocesos aislados, antes de pasar contexto local al LLM para su priorización.
*   **FR-006 [Multiplexed Output]:** La documentación se genera en al menos 4 canales simultáneos (`Technical`, `Human`, `AI_Context`, `Debt Analysis`).
*   **FR-007 [Intelligence Interface]:** Habilitar REST APIs para querying determinístico en JSON o consultas vía LLM (Context building) limitando las ejecuciones a 100 rpm/job.

---

# 05. Non-Functional Requirements

*   **NFR-001 [Cost Tracking Transparency]:** Exactitud en tokens input/output y costo USD grabados en `agent_executions` y consolidados en `jobs`.
*   **NFR-002 [Concurrency]:** Soportar múltiples jobs paralelos sin afectar el estado interno de la memoria compartida.
*   **NFR-003 [Resilience/Idempotency]:** Las escrituras en DB deben ser transaccionales. En caso de falla grave de un Agente, el Job muta a estado parcial/fallido.
*   **NFR-004 [Observability]:** Integración obligatoria de tracing en llamadas de LiteLLM (`Langfuse`).
*   **NFR-005 [Large Context Adaptability]:** Capacidad nativa del orquestador de fragmentar llamadas (`multi_zone` o `hierarchical_multi_zone`) si superan la ventana de contexto.

---

# 08. Core System Flows

**Flujo 1: Análisis Principal Pipeline (Asíncrono en Background)**
1.  Cliente (API) envía requerimiento iniciar Job.
2.  FastAPI crea Job en `Postgres`, invoca hilo asíncrono.
3.  `JobManager` clona repo a path temporal.
4.  Ejecución: `Task 1 (Stack)` -> `Task 2 (Architecture Context Heuristics)`.
5.  `SystemMapper` solicita clearance al `LLMBudgetService`. Se define estrategia `single|multi|hierarchical`.
6.  `Task 3` emite System Map JSON.
7.  `TechDebtAnalyzer` dispara linters en `subprocess`. Recolecta. Solicita clearance LLM, resume en Deuda Sistémica (Task 4).
8.  Punto de Paralelización (Tasks 5, 6, 7, 8 actúan simultáneamente para escribir Docs).
9.  Fin Job -> Se actualiza Postgres y se notifica vía Redis PubSub.

**Flujo 2: Build Task Context (Consulta Vía API)**
1.  Cliente POST `/jobs/{id}/build-task-context` "Requiero refactorizar módulo de login".
2.  FastAPI recupera Job.
3.  Servicio contacta al `LLMBudgetService` pidiendo clearance.
4.  LLM interroga los Documentos AI e inserta fragmentos para definir contexto seguro.
5.  Actualiza Budget. Retorna JSON final.

---

# 09. Business Rules

| Rule ID | Regla Funcional | Descripción / Implicación |
| :--- | :--- | :--- |
| **BR-001** | **Scope Singularity** | Cada Job analiza **únicamente un frente**. |
| **BR-002** | **Budget Hierarchy** | Si el `LLMBudgetService` determina que se excede el disponible y no puede degradar el modelo, **aborta el Job**. |
| **BR-003** | **No Auto-Coding** | El `RepoIntelligenceInterface` PROHÍBE mutar el código origen. CodeReborn genera documentación y contexto estructurado. |
| **BR-004** | **Hybrid Isolation** | Fase 1 de deuda es sub-proceso (Ej. pylint). Fase 2 es LLM interpretando los hallazgos de pylint. |
| **BR-005** | **Documentation Segregation** | Los 4 Writers paralelos no deben contaminar sus prompts entre sí para garantizar tonos únicos. |
