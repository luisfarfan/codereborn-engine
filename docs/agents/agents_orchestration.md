# 13. Agent System Specification

El núcleo de orquestación del análisis está soportado en **CrewAI**. Todos los Agentes reportan en una tubería dirigida.

### 13.1 Stack Detector
*   **Propósito:** Inferencia tecnológica agnóstica de infraestructura, frameworks y entrypoints.
*   **Tipo:** Determinista. Wrapper sobre Sub-process CLI.
*   **Tool Principal:** `specfy/stack-analyser` configurado vía sub-process shell.
*   **Pipeline:** 
    1. Ejecuta CLI tool sobre src_target. Extrae output RAW. 
    2. Agente (Script Type/Python) valida outputs con heurísticas secundarias (ej., busca `docker-compose.yml` que specfy pudiese omitir).
    3. Normaliza. Asigna `confidence_score` numérico. Emite informe `Stack Intelligence Report`.

### 13.2 Architecture Context Builder
*   **Propósito:** Generar una versión comprimida y legible del árbol de archivos, podando la basura para ahorrar Tokens durante la síntesis arquitectónica.
*   **Tipo:** Heurístico. Zero LLM calls.
*   **Comportamiento:** 
    Pondera centralidad basada en importaciones (Grafo) o estructura léxica. Excluye `/vendor` o `node_modules`. Establece ranking. Retorna JSON Context File representativo.

### 13.3 System Mapper (El Core Analítico)
*   **Propósito:** Interrogar y resolver los patrones arquitectónicos estructurales subyacentes frente al caos legacy. 
*   **Tipo:** Cognitive LLM. Token-Aware obligatorio.
*   **Comportamiento:** Contacta al `LLMBudgetService`. Analiza según modalidad recomendada (single, multi o hierarchical). Consolida una descripción teórica informando fronteras ("mixed architectures"). Provee las fundaciones a los demás LLMs.

### 13.4 Tech Debt Analyzer (Híbrido)
*   **Fase 1 (Determinista):** Lanza linters paralelamente (`ESLint`, `pylint`, complejidad ciclomática). Acumula listado (`finding_id` uuid).
*   **Fase 2 (LLM):** Extrae de BD el `SystemMap` + Top Linters Findings. El Agente sintetiza los problemas en dependencias ciclares sistémicas que frenan el proyecto. Retorna `Tech Debt Analysis Report`.

### 13.5 Doc Writing Layer (El Multi-Pool)
*   **Propósito:** Múltiples agentes documentadores separados. Si fuesen uno solo se excedería su context window y contaminarían los estilos narrativos.
*   **Típología:** Tareas CrewAI en paralelo o asíncronas no inter-dependientes.
*   **Output:** Graban masivamente a `doc_artifacts` PostgreSQL en base a los consumos previos del SystemMapper y el DebtAnalyzer.

---

# 15. Orchestration & Execution Model

Modelo de Event-Driven Job Execution. La API devuelve al usuario el ID de petición y todo el procesamiento toma entorno Async.

*   **Task Runners:** `JobManager` actúa como driver que despacha las misiones de CrewAI. 
*   **Manejo de Estado Job:** Persistido transaccionalmente a PostgreSQL. Updates inmediatos a cada paso de fase (Status de cada agent_execution guardado asíncronamente).
*   **Pub/Sub Global Limitado:** Redis Publisher solo se emite cuando termina un Job masivo, no para coordinar la tubería inter-agentes (CrewAI maneja su propio grafo sincrónico/local).
*   **Aislamiento y Garbage Collection:** El repositorio evaluado clona a volumen efímero en Worker VM. Obligatoria implementación de una Subrutina *clean_up_resources()* en estado "completed", "failed", o en Signal SIGTERM.
