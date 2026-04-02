# 06. Domain Model

**Context Boundaries:**

1.  **Job Context:**
    Representa el estado operativo y ciclo de vida de un request de análisis para un repositorio.
    *   `Job` (1 - 1) `StackReport`
    *   `Job` (1 - 1) `ArchitectureContext`
    *   `Job` (1 - 1) `SystemMap`
    *   `Job` (1 - 1) `TechDebtAnalysis`
    *   `Job` (1 - N) `DocArtifacts`
    *   `Job` (1 - N) `AgentExecutions`

2.  **Economic Context:**
    Gestiona la sustentabilidad de la ejecución basada en tokens para modelos privados/comerciales.
    *   `Job` ← `budget_config` (Presupuesto Base)
    *   `LLMCallDecision` (Auditoría antes de un llamado LLM)
    *   `AgentExecution` (Facturación deducida una vez ejecutada la orden)

3.  **Code Representation Context:**
    *   `FileClassification` (Metadata extraída sobre propósito y rankings arquitectónicos)
    *   `TechDebtFinding` (Deuda localizada e identificable)
    *   `Zone` (Agrupación lógica de subárboles AST para escalar con contextos grandes)

---

# 07. Actors and Roles

### Actores Externos
1.  **Client (User/IDE/MCP Client):** 
    Dispara los `Jobs` vía URL en la API, define los límites presupuestarios y el scope frontal. Consume los endpoints de la `RepoIntelligenceInterface` para guiar desarrollos, revisiones y onboarding.

### Componentes de Control (Sistemas)
1.  **JobManager (System Orchestrator):** 
    Motor asíncrono que delega recursos al inicio de un job. Maneja la clonación segura en un sandbox y elimina rastros del código legacy posteriormente.
2.  **LLMBudgetService (Gatekeeper):** 
    Actor crítico y pervasivo. Mantiene el control estricto sobre todo request de los agentes cognitivos. Define los fallbacks, zonas y truncados.

### Roles de Agentes Especializados (CrewAI Workers)
1.  **Stack Detector:** Especialista en análisis semántico de packages y binarios base.
2.  **Architecture Context Builder:** Especializado en métricas de grafos AST e inferencias por carpetas para podar el árbol y emitir sólo lo valioso arquitectónicamente.
3.  **System Mapper:** Analista Cognitivo en Jefe. Descifra inconsistencias de diseño.
4.  **Tech Debt Analyzer:** Revisor Híbrido, cruza fallas formales con deudas sistémicas.
5.  **Documentation Writers (4 Múltiples):** Redactores segmentados por público (Habilitadores de interfaces futuras).
