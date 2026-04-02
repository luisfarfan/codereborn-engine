# Componente 4: Tech Debt Analyzer

El `tech_debt_analyzer` funge como Agente del pipeline pero se define semánticamente como un componente "Híbrido". Está dividido operativamente en 2 pases secuenciales (Determinista Sub-shell + Cognitiva LLM Inference Limitada). 

Su propósito central es diagnosticar el grado de descomposición, obsolescencia o riesgo vital inherente de mantenimiento que posee el codebase analizado.

## Fase 1: Detección Determinística de Deuda (Raw Diagnostics)
Zero LLM Tokens gastados aquí. Dependiendo el lenguaje central detectado en la Fase 1 (`StackDetector`), el Agente levanta procesos síncronos aisaldos (runners) e inicializa la recolección masiva de warnings y alertas locales del Linter base asociado de CodeReborn.

1.  **Ruteador de Lenguaje Local:**
    *   `JavaScript / TypeScript` => Arranca *ESLint* (con reglas extremas hardcodeadas, enfocado en complexity y code smels), metricidad de copia (clone detection) y duplicidad de nodos similares.
    *   `Python` => Arranca *Pylint* + *Bandit* (Scanner SAST rápido nativo) + *Radon* (Reportador matemático de Maintainability Index global y complexity de MCCabe).
    *   `Java` => *SpotBugs* / *PMD*.
    *   `Go` => Binario gigante de *golangci-lint* activado con todos los submódulos on.

2.  **Mapeo de Alertas (Métricas Estructurales CodeReborn):**
    Adicionalmente a los binarios standard, el analizador local inyecta una cacería vía Regex pura y simple parsing directo para marcar y apilar Deuda Cruda de Formato: Archivos > 1000 LOC, funciones > 50 LOC, importaciones cíclicas duras (File A > File B > File A), y acoplamiento (fan-in / out exagerados). Localiza tags como `// TODO:` o `// HACK:`.
    
3.  **Persistencia Transaccional Temprana:** Almacena todos estos "Falsos Positivos" crudos y sucios. Cada hit ingresa a su ID en la tabla `tech_debt_findings` como una unidad atómica (un `finding_id`).

## Fase 2: Interpretación y Síntesis LLM (Correlación Sistémica)
Un LLM no necesita ver 5.000 alertas sueltas de pylint porque estallaremos el Budget. CodeReborn usa al LLM para actuar como un "Arquitecto Revisor Humano": Se le debe inyectar el N Top Ranking Crítico de fallas, cruzándolo con el `System Map Report` para poder identificar correlaciones profundas.

**Lógica del Gatekeeping:** Solicita aprobación del `LLMBudgetService` adjuntando los Top Findings Locales extraídos y el JSON del Mapeo Sistémico recabado en Agente 3.

**Razonamiento Pedido al LLM (El Prompt Inteligente):**
Identificar el `Lava Flow` (código viejo pudriéndose sin que nadie sepa si removerlo), `God Objects` y `Shotgun Surgeries`. La magia está en correlacionar: "Tengo 80 alertas seguidas locales sobre un archivo. Mirando el Map Report, ese archivo Resulta ser un Entity del dominio Core de Pagos. Eso denota una crisis sistémica de frontera."

## Output Target: Tech Debt Analysis Report
Persiste y responde el análisis filtrado depurado. Retorna consolidado de métricas relacionales, fallas de cohesión o acoplamiento graves. 

Este resultado va hacia la DB central en `tech_debt_analyses` listando prioridades de ataque (Qué curar primero para salvar el stack) y Quick Wins.
