# 24. Open Questions & Decision Gaps

*   `[GAP 1]` **Implementación Vectorial RAG:** El documento exige una capa REST donde los Agentes y Asistentes consulten y el backend *Arme* contextos on-the-fly (`/build-todo-context`). Esto habitualmente pide Bases de Datos Vectoriales. ¿Construiremos `PgVector` sobre la misma base central en el MVP para ahorrarnos configurar ChromaDB u otro cluster Standalone?
*   `[GAP 2]` **SLA/Timeouts Workers Asíncronos:** Análisis a un Monorepo de >5K archivos demoraría horas en orquestación Multi-Zone CrewAI. ¿Se implementa Background Tasks de FastApi? ¡No! Debe pasarse formalmente a Celery o ARQ (asyncio Redis Queue) para aislar latencias críticas HTTP de los requests. *Pendiente confirmación de Task Broker.*
*   `[GAP 3]` **Integraciones OpenMCP:** La API en `/jobs/{id}/*` tiene pinta de Modelo Servidor. ¿Crearemos los manifestos SDK para conectar Cursor automáticamente mediante el protocolo de transporte local Standard I/O (StdIO) o limitamos la V1 a integraciones vía HTTP?
*   `[GAP 4]` **Lifecycle Borrado Efímeros:** Cuando la Job falla "Parcialmente", ¿Eliminamos el Sandbox Repo local o lo preservamos temporalmente para fines de depuración manual del Engine?

---

# 25. Recommended Next Specs

Se aconseja como equipo líder Spec-Driven la ejecución de los siguientes artefactos, previa codificación general.

1.  *Data Definition Language File (DDL) y Modelo SQLAlchemy (SQLModel) final*. Generar toda la tabla relacional JSONB formal y sus índices GIN/PgVector.
2.  *Especificación Estricta de Interfaz RAG y Embeddings Strategy*. Estipular los parámetros exactos (Chunking Size) del Output JSON/Markdown de Documentación que será vectorizado.
3.  *Pruebas Estáticas Mínimas Viables (Fixture Set)*. Preparar 3 repositorios dummies estáticos, empaquetados en `.tar.gz`, representativos de (A) Front React Spaghetti (B) Python Django Legacy, de cara a inyectarlos a los workers locales saltando el cloning-network delays.
