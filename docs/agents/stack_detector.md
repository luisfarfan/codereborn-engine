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
1. **Normalización Semántica**: Estandarización de nombres de tecnologías y versiones.
2. **Directory Mapping**: Genera recursivamente el árbol de carpetas con conteo de archivos, tipos predominantes y profundidad. Vital para el `Pattern Detector`.
3. **File Inventory**: Clasifica cada archivo por lenguaje y tipo (code, test, config, doc, env) para obtener métricas volumétricas precisas.
4. **Service Scanning**: Parseo de Dockerfiles y `docker-compose.yml` para extraer servicios subyacentes (Redis, Postgres, etc.).
5. **Score de Confianza**: Cálculo algorítmico del `confidence_score` basado en la calidad de la evidencia encontrada.

## Output Target: Stack Intelligence Report
Este agente genera el output universal e inmutable (que será ingestado por el Resto de los Agentes en sus inputs). 
Se persiste a PostgreSQL en la tabla `stack_reports`. Responde al model:

```json
{
  "stack_summary": "Extracted string",
  "project_name": "Inferred from package.json/git",
  "analysis_scope": "frontend",
  "primary_language": "TypeScript",
  "languages": [{"language": "TypeScript", "estimated_percentage": 80.5}],
  "frameworks": [{"name": "React", "version": "18.0.0", "category": "ui"}],
  "dependencies": [{"name": "next", "version": "^14.0.0", "dep_type": "runtime"}],
  "services": [{"name": "Redis", "service_type": "cache"}],
  "infra_hints": [{"signal": "Vercel signals", "description": "vercel.json detected"}],
  "docker_hints": {"dockerfile_present": true, "compose_present": true},
  "build_tools": [{"name": "vite", "tool_type": "bundler"}],
  "entrypoints": [{"file_path": "src/index.tsx", "role": "main"}],
  "config_files": [{"file_path": "next.config.js", "config_type": "build"}],
  "file_inventory": {
    "total_files": 150,
    "by_language": {"TypeScript": {"total_files": 120, "total_lines_of_code": 12000}}
  },
  "directory_structure": {
    "root_directories": [{"path": "/src", "file_count": 80, "subdirectories": ["components", "hooks"]}]
  },
  "confidence_score": 0.98,
  "analysis_timestamp": "2024-04-04T12:00:00Z"
}
```
