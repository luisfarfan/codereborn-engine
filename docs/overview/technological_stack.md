# Stack Tecnológico Base de CodeReborn

El sistema se fundamenta en un ecosistema robusto de infraestructura y procesamiento paralelo, gobernado estrictamente bajo Python como lenguaje orquestador.

## 1. Tecnologías Base Mandatorias
*   **CrewAI:** Motor de orquestación de Agentes. Administra los roles, misiones, herramientas (Tools) y delegaciones (Delegation Rules) del pipeline analítico LLM. Cada agente es un 'Agent' de CrewAI.
*   **PostgreSQL:** El corazón transaccional del sistema. A diferencia de implementaciones triviales, CodeReborn guarda todo (estado, resultados, tracking de tokens, JSON's gigantescos de meta-data) de forma altamente relacional usando columnas JSONB.
*   **FastAPI:** Framework asíncrono para exponer la capa final de valor: el `repo_intelligence_interface`. Conecta la base de datos de manera determinística a las peticiones HTTP externas.
*   **specfy/stack-analyser:** Herramienta open-source CLI empleada por los agentes determinísticos como motor primario para la detección pura de stack.
*   **Redis (Opcional en Job pipeline, Mandatorio en infra):** Usado para PubSub y comunicación asíncrona pero CUIDADO: *Sólo* destinado a comunicación cruzada / señales de tiempo real inter-Jobs. El pipeline interno sincrónico NO usa Redis, usa la delegación en memoria nativa de CrewAI.

## 2. Paradigma de Comunicación de Agentes
La transmisión de conocimiento entre Agentes (Stack -> Context -> Mapper -> Debt -> Docs) se maneja puramente empleando las **Sequential Tasks** con Shared Context de CrewAI, no message brokers externos de ida y vuelta complejos para evitar fallas transaccionales a nivel de estado en medio de un pipeline de Job.
Las escrituras al terminar The Task sí impactan Postgres.
