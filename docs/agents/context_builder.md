# Componente 2: Architecture Context Builder

El segundo agente en la cadena de mando (`architecture_context_builder`) sostiene, al igual que el anterior, un enfoque radicalmente **Determinístico**. No realiza conjeturas de razonamiento generativo.

**Misión:** Construir el contexto idóneo. No importa qué tan grande o caótico sea el repositorio legacy. Su trabajo es podarlo, exprimirlo, fragmentarlo e indexarlo en un `Payload` estructurado matemáticamente para que el Agente Analítico Central (`SystemMapper`) no estalle por sobrecarga de tokens (token limit) ni contamine sus respuestas (Hallucination) con archivos triviales (basura boilerplate).

## Capacidad 1: Inspección y Crawling Heurístico
1.  **Directorio a Grafo:** Navega recursivamente el path base de código. Excluye por naturaleza carpetas como `.git`, `node_modules`, `vendor/`, `.venv`.
2.  **Clasificación Heurística Pura:** Emplea "Expresiones Regulares", nombres canónicos de framework (que arrastra de conocer el `Stack Intelligence Report` del componente anterior) y sintaxis de AST local (via herramientas como `tree-sitter` o `ast` en python).
3.  **Roles Arquitectónicos (Tags):** A cada archivo se le asigna un "rol probable". 
    *Ejemplos:* `controller`, `service`, `repository`, `entity`, `dto`, `test`, `frontend-component`, `frontend-page`, `event-handler`, `schema`.

## Capacidad 2: Ranking Matemático (El Valor Arquitectónico)
Todo archivo en un sistema no vale lo mismo. Los tests unitarios no informan igual que el `main.py` de inyección de dependencias. Para curar el Payload con inteligencia, calcula el *Ranking Arquitectónico*.
1.  **Fan-in / Fan-out:** Un archivo importado masivamente en todo sitio ostenta alto fan-in (Puede ser una Entity core). Un archivo que importa 90 clases de todos sitios denota alto fan-out (Puede ser el Dios Orchestrator Controlador o inyector principal). Ambos valen ORO.
2.  **Centralidad Estructural:** Archivos alojados en la raíz principal (`/src`) tienen mayor peso probabilístico que dependencias estáticas guardadas a 4 subcarpetas abajo.
3.  **Tamaño Racio:** Ficheros en blanco se descartan.

## Capacidad 3: Sampling y Zonas
Basado en lo previo, el agente parte lógicamente el árbol (ej, sub-folders principales) considerándolos formalmente una "Zona". Extraerá muestras crudas representativas (`architectural_samples`) del top ranking. Toma estas "Views" de código reales porque los algoritmos generativos como LLMs precisan ver sintaxis verdadera de firmas y clases para entender el dialecto de comunicación real.

## Output Target: Architecture Context Payload
Persiste un objeto masivo pre-computado sin IA, grabado a la tabla de Postgres `architecture_contexts`.

Contiene: `repo_tree_summary`, `file_classifications` (mapa de metadatos gigantesco), listado numérico `file_rankings`, `entrypoints` absolutos, sus muestras `architectural_samples`, y `import_graph_hints` pre-cocinados.
