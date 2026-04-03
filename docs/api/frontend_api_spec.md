# Frontend API Specification

Esta documentación cubre todos los endpoints diseñados para servir al frontend de CodeReborn. Complementa el documento `interfaces_and_api.md` que describe la Repo Intelligence Interface (orientada a agentes de IA).

## Principios de Diseño

- **Tier vs AnalysisMode**: El frontend habla de `tier` (budget/standard/premium). El backend usa `AnalysisMode` (economy/balanced/quality). El API layer hace el mapping; los agentes nunca ven el concepto de "tier".
- **`/agents` es estático**: El catálogo de agentes se define en código. No hay DB involucrada.
- **SSE via Redis PubSub**: Los agentes publican en Redis; el endpoint `/stream` hace forward al cliente. Redis solo para PubSub, nunca para datos de pipeline.
- **github_token nunca se devuelve**: El token se recibe en POST /jobs pero nunca se retorna en ningún response.

---

## Tier → AnalysisMode Mapping

| Frontend tier | Interno AnalysisMode | Modelos default |
|---|---|---|
| `budget` | `economy` | llama-3-70b, gpt-3.5-turbo |
| `standard` | `balanced` | gpt-4-turbo, claude-haiku |
| `premium` | `quality` | claude-opus-3.5, gpt-4-turbo |

---

## Endpoints

### GET /api/v1/agents
Catálogo de agentes disponibles y configuración de tiers. 100% estático.

**Response**: Lista de 8 agentes con `available_models[]` y 3 tiers con `default_models`.

Ver schema completo en `app/api/routers/agents.py`.

---

### POST /api/v1/jobs/estimate
Calcula el costo y duración estimados para un Job planificado. **Sin efectos secundarios** — no escribe en DB, no llama LLMs.

**Request**: Igual a `POST /jobs` (repo_url, tier, agent_configs[]).

**Response**:
```json
{
  "estimated_tokens_total": 125000,
  "estimated_cost_usd": 4.85,
  "estimated_duration_minutes": 18.5,
  "breakdown_by_agent": [...],
  "warnings": []
}
```

Lógica en: `app/services/estimation_service.py`

---

### POST /api/v1/jobs
Crea y encola un nuevo análisis.

**Request**:
```json
{
  "repo_url": "https://github.com/org/repo",
  "branch": "main",
  "github_token": "ghp_...",
  "tier": "standard",
  "agent_configs": [
    { "agent_id": "system_mapper", "enabled": true, "model": "gpt-4-turbo" }
  ]
}
```

**Response**: `{ job_id, status, created_at, started_at, repo_url, branch }`

**Nota**: El frontend navega inmediatamente a `/jobs/{job_id}` (live view).

---

### GET /api/v1/jobs
Lista Jobs del usuario con filtros.

**Query params**: `status`, `scope`, `tier`, `start_date`, `end_date`, `page`, `page_size`.

**Response**: `{ jobs: JobSummaryResponse[], total, page, page_size }`

Cada `JobSummaryResponse` incluye campos computados: `repo_name` (derivado de URL) y `duration_seconds`.

---

### GET /api/v1/jobs/{job_id}
Job completo con sub-recursos.

**Response**: Incluye `agents[]` (ejecuciones por agente), `outputs[]` (metadata de outputs disponibles), `logs{}` (URL + count).

---

### DELETE /api/v1/jobs/{job_id}
Cancela un Job en ejecución.

**Response**: `{ job_id, status: "cancelled", message }` (HTTP 200, no 204).

---

### GET /api/v1/jobs/{job_id}/outputs/{output_type}
Sirve un output artifact específico.

**output_type valores**: `stack_report`, `architecture_context`, `system_map`, `tech_debt_analysis`, `technical_doc`, `human_doc`, `ai_context`, `debt_doc`.

**Response**: `{ type, format: "json"|"markdown", content: <raw data> }`

---

### GET /api/v1/jobs/{job_id}/logs
Timeline de eventos de ejecución del Job.

**Response**: `{ logs: LogEntry[], total }` donde cada entrada tiene `timestamp`, `level`, `agent`, `message`.

Generado sintéticamente desde las filas de `AgentExecution` — no es un log file separado.

---

### GET /api/v1/jobs/{job_id}/stream
SSE endpoint para actualizaciones en tiempo real.

**Protocolo**: Server-Sent Events (EventSource en el navegador).

**Tipos de evento**:
| Evento | Cuándo |
|---|---|
| `ping` | Al conectar (keepalive inicial) |
| `job_status` | Update periódico de estado |
| `agent_started` | Cuando un agente empieza |
| `agent_progress` | Progreso parcial de un agente |
| `agent_output_chunk` | Streaming de output JSON |
| `agent_completed` | Agente terminó (success/fail) |
| `agent_communication` | Un agente pasa datos a otro |
| `job_completed` | Job terminó exitosamente |
| `job_failed` | Job falló |

**Cierre**: El stream se cierra automáticamente al recibir `job_completed` o `job_failed`.

**Redis channel**: `job:{job_id}:events` — los agentes publican aquí.

---

## Cómo los Agentes Publican Eventos

Los agentes (cuando se implementen) deben publicar en Redis así:

```python
import json
from app.infrastructure.redis_client import get_redis_client

async def publish_agent_event(job_id: str, event_type: str, data: dict):
    redis = await get_redis_client()
    await redis.publish(
        f"job:{job_id}:events",
        json.dumps({"event": event_type, "data": data})
    )
```

Ejemplo de evento `agent_started`:
```python
await publish_agent_event(job_id, "agent_started", {
    "agent_id": "system_mapper",
    "agent_name": "System Mapper",
    "started_at": datetime.utcnow().isoformat()
})
```
