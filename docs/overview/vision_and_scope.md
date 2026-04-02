# 00. Executive Overview

**CodeReborn** es una Plataforma de Inteligencia de Repositorios Legacy (Legacy Repository Intelligence Platform). Su objetivo primario es transformar un repositorio de código existente, a menudo desordenado o sin estructura canónica, en una base de conocimiento altamente indexable, consultable y viva.

A diferencia de los analizadores de código estático tradicionales, CodeReborn combina el **descubrimiento técnico determinista** con la **interpretación profunda LLM**, produciendo artefactos estructurados y proveyendo una interfaz (Repo Intelligence Interface) para ser consumida inmediatamente por humanos (Engineering Managers, Tech Leads), IDEs, coding assistants, y clientes MCP.

**Filosofía Core:** "No usar LLM para lectura de fuerza bruta". El sistema emplea un pipeline "embudo" donde heurísticas agnósticas extraen el contexto, y el LLM se restringe estrictamente al razonamiento algorítmico guiado bajo un control presupuestario milimétrico.

---

# 01. Source Interpretation

Este sistema se construye íntegramente bajo la filosofía de **Spec-Driven Development (SDD)**. La tubería de análisis recae en 6 (+1) componentes estrictos operando bajo CrewAI y FastAPI.

*   **Pilar 1: Reducción de Ruido:** El AST o la estructura de carpetas nunca se pasa completa y síncrona al LLM. Se somete a clasificación y "ranking de valor arquitectónico".
*   **Pilar 2: Economía:** Cero peticiones LLM ocurren sin validación previa del `LLMBudgetService`.
*   **Pilar 3: Adaptabilidad de Escala:** Implementación de partición dinámica ("zonas") basada en el tamaño en tokens del grafo resultante (`single_pass`, `multi_zone`, `hierarchical_multi_zone`).
*   **Pilar 4: Inferencia Híbrida:** Cruce de linters estándar con razonamiento semántico LLM para encontrar "deuda sistémica".

---

# 02. Product Vision

Convertir el "Legacy" en "Inteligencia Documentada". CodeReborn busca reducir drásticamente el tiempo de onboarding en código legacy, minimizando el riesgo arquitectónico en refactors mediante la provisión sistemática de "Puntos Seguros de Extensión", "Mapeos de Boundaries" y "Dossiers de Deuda Técnica".

---

# 03. Scope Definition

**In-Scope (V1):**
*   Pipelines asíncronos para análisis de un Job por vez.
*   Procesamiento de un único "Frente" o "Scope" a la vez (frontend, backend, mobile).
*   Repositorios con un stack tecnológico único dominante.
*   Cálculo y rastreo exacto de costos y tokens vía LiteLLM a Postgres.
*   Generación estática estructurada de contexto, patrones, riesgos y deuda técnica.
*   Exposición de inteligencia a través de API REST (FastAPI).

**Out-of-Scope (V1):**
*   Análisis Polyglot profundo simultáneo.
*   Multifrente automático.
*   Edición o alteración del código fuente analizado (no es un Auto-Coder).
*   Detección diferencial (git diff) para actualizaciones incrementales (se requiere nuevo Job para re-analizar).
