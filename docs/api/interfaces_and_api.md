# 12. API and Interface Contracts
# 16. Repo Intelligence Interface (MCP Layer)

Esta es la interfaz RESTful HTTP que abstrae la complejidad y el coste cognitivo de leer el repositorio crudo a los sistemas externos.

**Seguridad y Operación:**
*   Autenticación vía Bearer (JWT Token).
*   Rate limiting agresivo en endpoint contextuales (100 peticiones / minuto / job) vía Redis.
*   Posible adaptación natural a *Model Context Protocol (MCP)*.

**Distribución de Endpoints por Dominio:**

1.  **Domain 1: Project Understanding (Rápido, estático)**
    *   `GET /jobs/{job_id}/project-overview`
    *   `GET /jobs/{job_id}/stack-summary`
    *   `GET /jobs/{job_id}/architecture-summary`
    *   `GET /jobs/{job_id}/entrypoints`
    *   `GET /jobs/{job_id}/external-dependencies`

2.  **Domain 2: Structural Navigation (Búsqueda local GIN Index)**
    *   `GET /jobs/{job_id}/module-map`
    *   `POST /jobs/{job_id}/find-module-files`
    *   `POST /jobs/{job_id}/find-files-by-responsibility`
    *   `GET /jobs/{job_id}/high-value-files`

3.  **Domain 3: Task Context Building (Sintético, LLM Requiring)**
    *Endpoints pesados que contactan al BudgetService y generan consultas RAG.*
    *   `POST /jobs/{job_id}/build-task-context`
    *   `POST /jobs/{job_id}/build-refactor-context`
    *   `POST /jobs/{job_id}/get-existing-patterns-for-feature`

4.  **Domain 4: Change Impact & Risk (Mixto)**
    *   `POST /jobs/{job_id}/get-change-impact-context`
    *   `GET /jobs/{job_id}/get-high-risk-zones`
    *   `GET /jobs/{job_id}/technical-debt-summary`

5.  **Domain 5: Document Access (Direct Access)**
    *   `GET /jobs/{job_id}/docs/technical`
    *   `GET /jobs/{job_id}/docs/human`
    *   `GET /jobs/{job_id}/docs/ai-context`
    *   `GET /jobs/{job_id}/docs/debt`

6.  **Domain 6: Guided Tools (Sintético Consultivo)**
    *   `POST /jobs/{job_id}/suggest-implementation-approach`
    *   `POST /jobs/{job_id}/suggest-testing-focus-areas`

---

# 17. RAG / Context / Embeddings Strategy

Para suplir eficientemente el Domain 3 (Task Context Building) y partes del Domain 6:

**Estrategia V1 - Inferencia recomendada:**
El sistema debe utilizar una base de datos vectorial para ingerir de manera post-procesada los `doc_artifacts` (específicamente la salida del `ai_context_writer`), los `tech_debt_findings` globales y el `architecture_summary`.

Recomendación técnica: **PgVector sobre el clúster de Postgres actual**.
    *   Evita sobrecarga arquitectónica de un ChromaDB standalone.
    *   Al concluir el Pipeline de orquestación, una tarea final asíncrona vectoriza el resultado, convirtiéndolo en un índice `pgvector` indexable bajo algoritmos HNSW. Las consultas del API REST simplemente realizarán operaciones `vector <=> queries` + un Reranker para entregar el "Contexto" al modelo LiteLLM final y devolver la directriz al cliente en el Response HTTP.
