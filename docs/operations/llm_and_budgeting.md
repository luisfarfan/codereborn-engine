# 14. Token & Cost Tracking System (CRÍTICO)

La sostenibilidad financiera del CodeReborn Engine recae exclusivamente sobre la gestión del sistema de tracking.

1.  **Mecanismo de Intercepción:** Todo Agente (CrewAI o Router) no tiene permitido generar `Prompt > OpenAI/Anthropic/Gemini` de manera directa. 
2.  **Servicio de Gatekeeper - LLMBudgetService:**
    *   Input: `Job_ID`, `Target Model`, `Context Estimado (Tokens tiktoken)`.
    *   Lógica: Busca JSON `budget_config` en el model `Job`. Extrae limitantes de Token Limit y Cost Limit del cliente. Calcula multiplicador tarifado vs. token input/output restante del bucket.
    *   Si APRUEBA, genera tupla temporal `LLMCallDecision` (Approved, Mode seleccionado).
    *   Si EXCEDE la ventana superior del modelo seleccionado, emite comando para fragmentar la búsqueda (Chunking/Multi-Zone mode) o, de ser imposible la degradación, detiene toda recursiones de la tubería del Job actual y dispara "FALLA FINANCIERA / TOKENS EXCEDS".
3.  **Registro y Liquidación:**
    *   Cuando LiteLLM o el backend completan la redada sobre el Foundational Model, retornan la metadata real `input_tokens` | `output_tokens` | `pricing`.
    *   Se efectúa un Commit a `agent_executions` de PostgreSQL, actualizando simultáneamente los agregadores de saldo remanentes del `Job`.

---

# 18. LLM Usage Strategy

Esquema "Model-Fallbacks" y especialización sugeridos apoyados sobre `LiteLLM` router (inferencia técnica).

**TIER 1 (Deep Reasoning Model)**
*   USO: `SystemMapper`, `TechDebt Synthesis`, y API Queries complejas (Domain 6 Guided Tools).
*   MODELOS IDEALES: `GPT-4o`, `Claude 3.5 Sonnet`, `Gemini 1.5 Pro` (Manejan ventana de contexto vasta para las uniones multi-zone y heurísticas crudas).
*   PERFIL: Alto Costo USD. Lento, profunda lógica de deducción topológica.

**TIER 2 (Content Writers)**
*   USO: Agentes Escritores del Scope Documental (`Technical`, `Human`, `Debt`, `AI_Spec`).
*   MODELOS IDEALES: `Claude 3 Haiku`, `GPT-4o-mini`, `Gemini 1.5 Flash`.
*   PERFIL: Medio-Bajo Costo USD, Rapidez Absoluta, Gran control sobre el tono narrativo. No deben inferir código, se dedican a reordenar datos del TIER 1.

**TIER 3 (Reserva y Degrader Presupuestario)**
*   USO: Cuando una petición preflight es detenida por presupuesto limitado en TIER 1 y el BudgetService dictamina intentar bajar calidad antes de abortar. Se reintenta el prompt con un modelo TIER 2 o un TIER 3 Hyper-cheap.
