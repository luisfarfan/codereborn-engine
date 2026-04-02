# Pipeline Core y el LLM Budget Service (Gatekeeper)

## 1. El Pipeline Conceptual Secuencial
El motor orquesta la ejecución a través de 6 componentes estructurales, forzando un embudo donde cada eslabón reduce el ruido para el siguiente:

1.  *(Servicio Transversal Autoritario)* `llm_budget_service`
2.  `stack_detector` (CrewAI Agent / Determinista)
3.  `architecture_context_builder` (CrewAI Agent / Determinista)
4.  `system_mapper` (CrewAI Agent / Cognitivo)
5.  `tech_debt_analyzer` (CrewAI Agent / Híbrido)
6.  `doc_writing_layer` (Pool of Agents / Paralelos Cognitivos)
7.  `repo_intelligence_interface` (Capa Consumidora Final / FastAPI)

---

## 2. Componente 0: LLM Budget Service (El Controlador del Tesoro)

El `llm_budget_service` **NO ES UN AGENTE DE CREW AI**. Es un componente utilitario "hardcoded", determinista y brutal, que funciona como API interna que intercepta y aprueba TODA llamada de un agente antes de que suceda.

### Responsabilidad Directa
Garantiza la supervivencia operacional del sistema, evaluando si hay "presupuesto en tokens/dólares". Previene llamadas ciegas fallidas. Toma la decisión del fallback, partición o rechazo.

### Algoritmo de Flujo del Gatekeeper
**[Paso 1: Estimación]** Utiliza TikToken (o estimador ligero de llm) para evaluar el Payload Input String inyectado por el Agente.
**[Paso 2: Evaluación]** Compara la variable `Tokens` contra el límite máximo del Modelo (Context Window) y contra el presupuesto disponible persistido en PostgreSQL bajo el Job actual (`max_tokens`, `max_cost_usd`).
**[Paso 3: Veredicto y Estrategia]**
*   *CASO IDEAL:* Aprueba el prompt. Emite señal modo `single_pass`.
*   *CASO EXCESO POR TOKEN MAX:* La Plataforma aprueba la viabilidad monetaria pero el payload "no entra". Gatekeeper emite señal: Convertirse en Modo `multi_zone`. Interviene retornando el cálculo exacto de a "cuántos asimétricos JSON Chunk Zones" debe cortarse.
*   *CASO DEGRADACIÓN FINANCIERA:* Si el job sobrepasó el 90% (o margen) de su costo presupuestado (dólares), emite orden de *Model Fallback* (Ej. Degradar de GPT-4o a GPT-4o-mini).
*   *CASO ABORTO (OOM Financial):* Abstinencia total de generación. Lanza una Excepción, marcando la tarea como Rechazada.

### Output del Sub-Sistema: Objeto LLMCallDecision
Este objeto de Python (Persistido luego a Postgres) se inyecta de regreso al Agente solicitante:
```json
{
  "approved": true,
  "model": "gpt-4-turbo",
  "mode": "single_pass | multi_zone | hierarchical_multi_zone",
  "chunks": 4, 
  "chunk_configs": {},
  "estimated_input_tokens": 45000,
  "estimated_output_tokens": 1500,
  "estimated_total_tokens": 46500,
  "estimated_cost_usd": 0.45,
  "warnings": ["Warning: Degradado de Multi-Zone por Budget Threshold a punto de cruzar límite"],
  "rejection_reason": null
}
```

## 3. Post-Llamado (Token & Cost Tracking Real)
Después de confirmada y ejecutada la llamada a la IA vía `LiteLLM`, el agente que ejecutó *debe* registrar los valores verdaderos retornados por el Endpoint Comercial OpenAI/Google.

Obliga a que cada tarea LLM culmine con una escritura ACID transaccional a la tabla de Postgres `agent_executions` grabando sus:
*   `input_tokens` reales.
*   `output_tokens` reales.
*   `cost_usd` fraccionado con absoluta exactitud analítica.
Y por fin, empaquetarlo sumando un += al global del Master `Job`.
