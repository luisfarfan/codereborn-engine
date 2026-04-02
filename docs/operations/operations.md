# 19. Security Model

1.  **Autenticación API:** Mapeo de Bearer JWT token estático de App mediante Auth Middleware en FastAPI. [GAP: Requerir integración OAuth si muta a SaaS].
2.  **Repo Cloning (Sandboxing):** Los repositorios descargados con credenciales (PATs) deben clonarse en Directorios EFÍMEROS locales, preferiblemente in-memory volumes si la RAM lo permite. **DEBEN ELIMINARSE** al término del Job.
3.  **Filtrado de Secrets:** El `TechDebtAnalyzer` y `StackDetector` (SAST) se limitará a informar fallas de codificación (ej., contraseñas hardcodeadas), bloqueando o emascarando (redact) la cadena real de la base de Datos, por seguridad.

---

# 20. Observability & Monitoring

Orquestar LLMs requiere mitigación severa a la opacidad operacional.
*   **Langfuse Tracing:** Extensión a `LiteLLM` inyectando traces por Agente e Interacción. Visible por `job_id`. Proporciona logs de Petición/Inferencia reales enviados a proveedores, posibilitando depurar las Alucinaciones de la máquina en un Panel gráfico a posteriori.
*   **Application Logging:** Consola JSON (Estándar ASGI). Mínimo Producción `INFO`. Local `DEBUG`.

---

# 21. Failure Modes & Risk Analysis

*   **Riesgo 1: Token Overflow (El Repositorio es brutalmente inmenso).**
    *   *Mitigación:* Si la sub-rutina `hierarchical_multi_zone` falla porque aún la unidad atómica mínima de carpeta revienta el Context Window, el Backend de `SystemMapper` forzará el estado general DB a `partial_done`. Interrumpiendo el cobro.
*   **Riesgo 2: Bloqueo Asíncrono de Hilo CPU (Parsing Loop).**
    *   *Mitigación:* Los Parsers Linters (GolangCI/ESLINT C++) disparados en Subproceso Python, forzarán **Timeout Abort (SIGKILL)** luego de Max Timer límite.
*   **Riesgo 3: LLM Output Formatting Error JSON.**
    *   *Mitigación:* Todos los Agentes exigen formato estricto (vía Pydantic Parsers en CrewAI). En caso de reintentos infructuosos, degrada el agente y persiste el string RAW marcando WARNING en el Task Status.

---

# 22. Testing Strategy

1.  **Dogfooding (On Itself):** La Validación Oficial 01 consiste en pasar el propio Stack y Código fuente de *CodeReborn* a Mapear por sus Agentes, verificando congruencia.
2.  **Mocking API:** Mock extensivo sobre el LLMBudgetService y Respuestas LITE LLM (vía Responses o MagicMock) para probar resiliencia con saldos `0` USD.
3.  **AST Trivial Fakes:** Alimentar el Agente ArchitectureBuilder `input_payload` falsos que asemejen un sistema MVC roto, probar si la inferencia es consistente localmente sin clonar código repetidamente.

---

# 23. Scalability & Performance Considerations

*   **Evitar Bloat Base De Datos:** Payload Raw masivos del Ast Graph consumen caché. Indexar únicamente la taxonomía.
*   **Stateless LLM Logic:** Módulo CrewAI debe recuperar y persistir su "Memoria" vía IDs a PosgreSQL. Ningún Agente mantiene estados en RAM VM permanente. Permite instanciar `M` workers sobre AWS ECS o EKS y consumir la cola `Redis` independientemente asegurando escabilidad horizontal robusta.
