# Scope del Análisis y Modos de Ejecución

## 1. Unicidad del Scope Funcional (Analysis Scope)
Cada invocación (`Job`) en el sistema está diseñada para atajar, comprender y procesar **UN SOLO FRENTE** a la vez.
**Restricción Estricta:** Un Job jamás debe mezclar código del backend y del frontend simultáneamente (ej: un monorepo React/Django en la misma raíz debe particionarse conceptualmente).

**Valores Válidos (El Enum `analysis_scope`):**
*   `frontend`
*   `backend`
*   `mobile`
*   `desktop`
*   `library`
*   `worker`
*   `other`

> *Nota a Futuro:* El sistema no gestiona repositorios polyglot (multipropósito mezclado en un mismo frente) en la versión actual. La orquestación manual de jobs por carpeta/frente es requerida.

## 2. Los 3 Modos de Análisis Dinámicos
La varianza en la cantidad de archivos es la amenaza real para el contexto límite del LLM y la billetera. Para lidiar con esto, el sistema muta entre 3 modos de aproximación de manera algorítmica.

IMPORTANTE: "Multi-zone" no es un concepto de dominio arquitectónico (no significa Microservicios), es un hack operacional (una partición de contexto) para fraccionar envíos hacia el LLM cuando el peso en "Tokens" del código es masivo.

### A. Modo `single_pass`
*   **Condición:** El tamaño en Tokens del repositorio cabe fluidamente en la Ventana de Contexto (Context Window) del Foundational Model.
*   **Ejecución:** El pipeline se ejecuta de principio a fin, enviando el input de contexto de una sola vez hacia el Agente.

### B. Modo `multi_zone`
*   **Condición:** El contexto supera el límite de un solo Prompt o el max_tokens asignado por dinero.
*   **Ejecución:** El componente inteligente agrupa los archivos en clústeres artificiales (módulos, domains, etc). Se orquestan "N" peticiones en paralelo (1 prompt al LLM *por zona individual*), y luego se lanza un último Prompt final de "Consolidación" solicitándole al LLM unir las piezas sueltas de las N zonas previas en un mapa global.

### C. Modo `hierarchical_multi_zone`
*   **Condición:** El repositorio es un titán enterprise (Miles de archivos). Incluso las "Zonas" superan el Token limit.
*   **Ejecución:** Un árbol de procesamiento. Las Zonas se parten en "Sub-Zonas". Se analiza la Subzona -> Se consolida en Zona madre -> Se consolida en el Mapa Global.
