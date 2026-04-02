# Componente 6: Repo Intelligence Interface (API Layer)

Este componente suplanta por completo el antiguo concepto de `mcp_generator` estático. No es una herramienta transaccional ni un exportador.
El **Repo Intelligence Interface** es un servidor en caliente, una **REST API (FastAPI)** robusta provista para responder en base al conocimiento recolectado de Postgres u orquestar Mini-Agentes Consultivos (RAG) para dar insights técnicos hiper-veloces.

NO edita código. NO genera PRs. **Sirve datos y consejo**.

## Modelado Seguro
Toda petición externa que golpee a la API debe estar respaldada por Token Portador (`Bearer <jwt>`).
A fin de proteger gastos excesivos a cuentas de desarrolladores o denegaciones de servicio involuntarias, una capa global Middleware `Redis` debe implementar fuertemente la regla impuesta: `<Limit=100_Requests_Minuto_Job>`.

## Dominio Categorizado de Capacidades (Las Rutas CRUD)
La interfaz expone endoints categorizados bajo 6 dominios puros orientados a suplir los miedos primordiales del mantenimiento a código heredado:

### 1. Project Understanding 
*Endpoints súper rápidos para extraer JSON y texto crudo. (No envían LLMs calls, traen info directa del DB).*
*   `GET /jobs/{job_id}/project-overview`
*   `GET /jobs/{job_id}/stack-summary`
*   `GET /jobs/{job_id}/architecture-summary`
*   `GET /jobs/{job_id}/system-style`
*   `GET /jobs/{job_id}/entrypoints`
*   `GET /jobs/{job_id}/external-dependencies`
*   `GET /jobs/{job_id}/data-flow-summary`

### 2. Structural Navigation
*Endpoints de búsqueda, equivalen a usar CTRL+P / Buscadores de Archivos, pero apalancados con semántica heurística extraída anteriormente.*
*   `GET /jobs/{job_id}/module-map`
*   `POST /jobs/{job_id}/find-module-files`
*   `POST /jobs/{job_id}/find-files-by-responsibility` → Ej: Body `{responsibility: "stripe payments"}`.
*   `GET .../code-zones`, `GET .../high-value-files`
*   `POST .../find-files-related-to-domain`

### 3. Task Context Building
*Generadores Lentos Cognitivos. Sometidos Obligatoriamente a LLMBudgetService.*
Sirven para fabricar un "Contexto de Prompt Seguro" que pueda ser arrastrado hacia ChatGPT/Claude/Cursor cuando un developer necesita abordar un ticket complicado y desea que esos bots no escriban el código donde no va, dictándoles las fronteras detectadas orginalmente en el pipeline de análisis.
*   `POST /jobs/{job_id}/build-task-context`
*   `POST /jobs/{job_id}/build-feature-context`
*   `POST /jobs/{job_id}/build-bugfix-context`
*   `POST /jobs/{job_id}/build-refactor-context`
*   `POST /jobs/{job_id}/get-recommended-files-to-modify` → Cruza tu string de intención contra el mapa para sugerirte qué tocar.
*   `GET /jobs/{job_id}/get-safe-extension-points` y `/get-existing-patterns-for-feature`

### 4. Change Impact and Risk
Evalúa estallidos posibles de dependencia. Sirve para mitigar si te animas o no a lanzar una PR que cambie una Entidad Base profunda.
*   `POST /jobs/{job_id}/get-change-impact-context`
*   `POST /jobs/{job_id}/get-dependency-impact` → ¿Quién se rompe si toco Auth.js?
*   `GET .../get-high-risk-zones`, `GET .../technical-debt-summary`

### 5. Documentation Access
Canilla sin filtros de acceso plano a la tabla `doc_artifacts` (Generados por los 4 Writters paralelos).
*   `GET /jobs/{job_id}/docs/technical` ... `human` ... `ai-context` ... `debt`
*   `GET /get-onboarding-summary`, `GET /get-developer-guide`

### 6. Guided Intelligence Tools
Mini Agentes Síncronos sobre Endpoints HTTP. Requieren Modelos Tier 1 caros para pensar soluciones algorítmicas en vez de ti. Interceptados por Budget.
*   `POST /jobs/{job_id}/suggest-implementation-approach`
*   `POST /jobs/{job_id}/suggest-refactor-strategy`
*   `POST /jobs/{job_id}/suggest-debugging-entry-points`
*   `POST /jobs/{job_id}/suggest-investigation-plan`
*   `POST /jobs/{job_id}/build-architecture-consultation-context`
