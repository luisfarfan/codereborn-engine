# Base de Datos: Schema y Persistencia Core

A diferencia de experimentales local-agent sandboxes, **CodeReborn** tiene una vocación Enterprise y asíncrona. La trazabilidad y robustez lo es todo. Por lo tanto, TODO output intermedio a lo largo del orquestador debe alojarse estáticamente en PostgreSQL antes de pasar a la siguiente etapa de pipeline.

Esta decisión otorga la posibilidad de reanudar un job roto desde el punto exacto donde falló el `Model Context` o donde se acabó el saldo del cliente, sin tener que pagar la ingesta de nuevo en tokens.

## Entidades Maestras Detalladas en DDL Abstracto

### 1. `jobs` (La Entidad Raíz)
| Campo | Tipo | Definición |
| :--- | :--- | :--- |
| `id` | UUID (PK) |
| `repo_url`, `repo_path` | STR | Git base URI, Cloned efímero OS Path. |
| `analysis_scope` | VAR | Ej: frontend, mobile... |
| `status` | ENUM | pending, running, completed, failed, partial |
| `budget_config`| JSONB | Límites monetarios/tokens máximos y soft limits de alerta. |
| `tokens_used`, `cost_usd` | INT/DEC | Tracking agregador. (Actualización post-tarea-hija). |
| `started_at`, `error_detail`| TS/TEXT| Control de fallas global. |

### 2. Entidades de Auditoría Administrativa (Finanzas y Ruteo)
*   **`llm_call_decisions`**: Cada pre-flight request capturado por el GateKeeper, contesta una `CallDecision`. Guarda el momento, `agent_name`, `approved`, el Modelo final, los Chunks si ordenó un Particionado dinámico, y el costo de token propuesto (estimación).
*   **`agent_executions`**: Cierre Transaccional Posterior de cada run. ID Job. Estado. La "Factura" final (`tokens_used` dictados por LiteLLM verídicos + USD equivalentes generados del provider). Toma nota de la duración y error.

### 3. Entidades Core de Análisis (Los Outputs Oficiales Json)
Se aboga fuertemente en el `PROMPT.AI` a depender del soporte `JSONB` que traen las bases PostgreSQL modernas (10+) en vez de construir relaciones relacionales estáticas `Table_A`->`Table_B` excesivamente verbosas, pues cada Framework Legacy de código es diferente e ignora reglas estándar. Todo Report output es almacenado nativamente como un Dict de Mongo.

*   `stack_reports`: FK->Job. Arrays de Frameworks, DBs, lenguajes detectados en %s y confidence scores.
*   `architecture_contexts`: FK->Job. Metadata monstruosa del Crawl de Archivos. File classifications, rankings, zones, y entrypoints puros para su inyección. 
*   `system_maps`: FK->Job. Generado del Sistema Cognitivo Principal. Patrones dominantes detectados, Consistency level.
*   `tech_debt_findings`: (Nota: ¡Ésta no solo es JsonB!). Posee un `finding_id` transaccional. Es plana para guardar las 4000 alertas sueltas por separado en la BD procedentes de los Lints sub-process (pylint, go-lint etc). Mantiene Severity, lineNumber, Category y Rule.
*   `tech_debt_analyses`: Summary Inteligente. Output cognitivo general sistémico agrupando miles de las anteriores bajo 3 o 4 Quick Wins globales.

### 4. Entidades Documentales y Contrato Final
*   **`doc_artifacts`**: Persistencia Múltiple del Grupo de Escritura Paralelo (Los 4 Writers). Formato (Markdown vs JSON stringified). UUID, Timestamp.

> **Importancia RAG Futura:** Esta topología base con JSONB ya preparará naturalmente la cancha si se decidiere migrar una parte de esos Docs a extensión Vectorial Local `PgVector` simplemente agregando una columna `embedding` (VECTOR 1536) directo sobre el renglón de un documento generado en la base SQL relacional, ahorrando sincronía contra la inestable DB externa ChromaDB en v1.
