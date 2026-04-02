# Orquestación, Concurrencia y Comunicación

El sistema abandona los conceptos de pipelines monolíticos síncronos en favor de paralelización pura sobre **CrewAI**, pero bajo férreas reglas de topología comunicacional para garantizar la idoneidad transaccional trans-evento.

## Mecanismo de Pasaje de Mensajes
La comunicación no se lleva a cabo mediante RabbitMQ ni RPC directos entre Agentes para no introducir fallas de red intra-nodo en el proceso crítico de razonamiento. Se utiliza **Memoria de Contexto Compartida (Shared Context)** nativa en CrewAI amparada en Listas u Objetos de Python en RAM durante las horas de ejecución.

### Grafo de Dependencias Seriales
El Grafo es Secuencial Dirigido en las Fases "Agnósticas e Inferencia Primaria", bloqueantes por diseño.

1.  Task 1: (Comienza) `Stack Detector` → Out SQL (Guarda Report SQL).
2.  Task 2: Inicia `Arch Context Builder`. Su input es el output en RAM de Task 1. → Guarda Out SQL.
3.  Task 3: Inicia `System Mapper`. Su input es Task 1 y Task 2. Carga, analiza con Gatekeeper LLM. → Guarda Out SQL.
4.  Task 4: Inicia `Tech Debt Analyzer`. Input: Task 1 y Task 3 (Para no ser falso positivo ciego). Alerta Lints + Sistémica. → Guarda Out SQL.

### Nodo de Paralelización Extrema (Brancheo)
Llegado al éxito de la Tarea 4, el Grafo CrewAI puede abrirse a Ejecución Concurrente Multihilo en el Pool "Doc Writing Layer".
5. Las tareas 5 (`Tech Docs`), 6 (`Human Docs`), 7 (`AI_Spec`), y 8 (`Debt_Docs`) arrancan a procesar SIMULTÁNEAMENTE sin esperarse entre ellas. Ingieren los Output de Task 1,3 y 4. Ninguna depende del output literario de su hermano paralelizado.

## El Rol de Redis y la Concurrencia Intra-Server
El Motor debe poder aguantar `N` Jobs solicitantes desde FastAPI en paralelo sin que interfieran sus directorios ni agentes (Thread Pool Limitation).

*   **PubSub de Redis:** Restringido EXCLUSIVAMENTE para Event-Sourcing Administrativo y Observabilidad externa. Cuando un Módulo FastAPI genera un POST nuevo sobre el RepoIntelligence, Redis publicará a WebSockets clientes para armar un Loader bonito en UI de "Progreso Tarea N/8" hacia el usuario Frontal. 
*   **Prohibición Expresa:** REDIS NO SE USA PARA TRASEGAR DATA ENTRE LOS CREWS DE TAREAS INTERNOS 1-8. Se evita llenar el socket de un In-Memory cache con JSONS de 6 Megas y un Context Window monstruoso de tokens que la matarían. El In-Memory corre limpio sobre RAM del Proceso aislado Python o de SQL si fuera extremadamente largo.

## Sandbox Aislado y Versión
-   CodeReborn clona 1 vez al empezar. Ejecuta 1 sola pasarela estática. No analiza ramas en tiempo real escuchando Webhooks (Out of Scope V1).
-   Se precisa que el Motor de Orchestración provea garantías imperativas de destrucción de Sandbox (`repo_path_local` `rm -rf`) cuando el Estado Transaccional dictamine que completó, falló abruptamente (kill sign -9) o que expiró su límite parcial de dinero.
