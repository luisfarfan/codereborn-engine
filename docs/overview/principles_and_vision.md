# CodeReborn: Principios Core y Visión del Producto

## El Propósito Fundamental
**CodeReborn** es un ecosistema avanzado de "Inteligencia de Repositorios Legacy". Su propósito único no es ser un analizador estático banal (como un linter convencional) ni un "lector de repositorios de fuerza bruta" impulsado por LLM. 
Debe comportarse como un **Motor de Inteligencia Técnica** que ingiere código legacy caótico, lo comprende con profundidad algorítmica y lo transforma en conocimiento estructurado, vivo, consultable y altamente reutilizable tanto para agentes autónomos (vía API/MCP) como para desarrolladores humanos.

## Principio Central del Sistema (SDD Core)
El sistema impone un límite severo y una separación absoluta del trabajo para garantizar economía, determinismo y prevención de alucinaciones. El pipeline se divide en tres filosofías de ejecución:

1. **Detección Objetiva y Determinística:** Tareas mecánicas, de extracción (parsers, CLI tools, AST basic crawlers) que no requieren inferencias. No se gasta 1 solo token (Ej. Identificar que existe un `package.json`).
2. **Preparación Inteligente de Contexto:** Procesamiento de grafos y heurísticas locales para podar el ruido. Reducir el codebase a las piezas fundamentales antes de despertar a la máquina cognitiva.
3. **Razonamiento e Interpretación:** Terreno reservado estrictamente para los Agentes LLM. Se utiliza *únicamente* cuando el problema exige síntesis, cruce de dominios, juicio arquitectónico o reconstrucción conceptual (Ej. "Este grupo de clases conforma un anti-patrón de God Object que compromete la capa de Dominio").

**Regla Cero:**
> "El sistema no debe usar LLM para todo. Debe usar lógica determinística cuando una tarea puede resolverse con inspección, parsing, heurísticas o herramientas existentes."

## Objetivo Final del Sistema
Convertir un frente legacy en:
1. Un entendimiento estructurado del stack tecnológico.
2. Un mapa real y fehaciente de su arquitectura (no una asumpción canónica).
3. Una lectura contextualizada, profunda y priorizada de su deuda técnica.
4. Una suite de documentación especializada por audiencias.
5. Una interfaz de inteligencia del repositorio (Repo Intelligence Interface) reutilizable por IDEs, MCPs y workflows de agentes en el futuro. 

CodeReborn reduce drásticamente el costo de onboarding, prepara contextos ultra-refinados para IA (coding assistants) sin obligarlos a leer miles de archivos, y ayuda activamente a líderes técnicos a trazar refactors seguros.
