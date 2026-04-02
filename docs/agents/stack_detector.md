# Componente 1: Stack Detector

El `stack_detector` es el primer agente operativo dentro del CrewAI Pipeline. 
Es una pieza intrínsecamente y estrictamente **Determinística**. Esto significa que *no gasta tokens de inferencia LLM en absoluto*.

Su responsabilidad se abstrae al descubrimiento de "QUÉ" tecnologías habitan en el repositorio, mas no "CÓMO" están arquitectadas. No le interesa si el Python está en un MVC o en Hexagonal; solo constata la presencia nativa de las herramientas.

## Integración Tool Principal (CLI Wrapper)
El componente actúa como un intermediario (wrapper) que invoca la herramienta binaria open source: `specfy/stack-analyser`. 

1. Levanta un subproceso shell local en el worker pasándole la ruta base del repo clonado efímero.
2. `specfy/stack-analyser` realiza crawling nativo rápido buscando y validando `package.json`, `pom.xml`, `requirements.txt`, etc.
3. El Agente captura el STDOUT JSON crudo de Specfy.

## El Motor Post-Procesador Python/CrewAI Subyacente
Specfy es genial, pero el output crudo carece de uniformidad y convenciones extra. Inmediatamente tras la captura del STDOUT, el bloque Post-Processor interno del `stack_detector` arranca una heurística complementaria que rellena los *gaps*.

### Evaluaciones Post-Proceso:
1. Normalización semántica de strings y frames detectados.
2. Lectura directa determinista (Regex/FileSearch) de entrypoints probables que specfy obvia (Ej: `App.tsx`, `main.py`, `server.js`).
3. Parseo agudo de Dockerfiles detectados o `docker-compose.yml`, intentando extraer servicios subyacentes mapeados localmente (redis cache image, posgres image port, etc).
4. Generación algorítmica de un `confidence_score` (0.0 al 1.0) sobre la veracidad del lenguaje principal asumido frente a la evidencia volumétrica.

## Output Target: Stack Intelligence Report
Este agente genera el output universal e inmutable (que será ingestado por el Resto de los Agentes en sus inputs). 
Se persiste a PostgreSQL en la tabla `stack_reports`. Responde al model:

```json
{
  "stack_summary": "Extracted string",
  "project_name": "Inferred from package.json/git",
  "analysis_scope": "frontend",
  "primary_language": "TypeScript",
  "languages": [{"name": "TypeScript", "pct": 80.5}],
  "frameworks": ["React 18", "Next.js 14"],
  "dependencies": {},
  "services": ["Docker Redis", "MySQL"],
  "infra_hints": ["Vercel signals", "AWS amplify config detected"],
  "docker_hints": {"dockerfile_exists": true},
  "build_tools": ["vite", "tsc", "make"],
  "entrypoints": ["src/index.tsx", "src/server/init.ts"],
  "config_files": ["tsconfig.json", "next.config.js"],
  "confidence_score": 0.98,
  "unknowns": []
}
```
