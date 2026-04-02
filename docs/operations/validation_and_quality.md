# Calidad, Validación Táctica y Cimientos del Sistema

CodeReborn impone, en su recta final de documentación original, la métrica con la cual el Engine será aprobado para pasarela Beta de Producto final.

## 1. Plan de Validación Escalonado (Roll-Out)
No se agregarán modulos futurísticos ni "Auto-Fixers" PR Automáticos a ciegas. La validación consta de someter este SDD al choque con la realidad legacy, testeando con repos probetas y contrastando la tasa de utilidad real (Dog-food metrics).

**Frentes requeridos para ser marcados como PASS (Criterio de Aceptación):**
*   *Small tier:* Repositorios < 100 archivos (Ej tests locales de unit fixtures minimalistas).
*   *Medium tier:* 100 a 500 archivos.
*   *Large tier:* 500 a 2000 ficheros de código orgánico.
*   *Monstruos Legacy:* > 2000 de código acoplado espagueti. Aquí se medirá violentamente si el MODO `Hierarchical_Multi_zone` no estalla el `Timeout` Límite del entorno FastAPI y Celery Worker, y si corta la hemorragia de tokens vía `Chunkings` limpios.

Se deben ingestar repositorios reconocidamente rotos por comunidad (Ejemplo de malos enfoques, arquitecturas de componentes inestables en React global scope) y verificar si la AI infiere "esto es Spaguetti" (ÉXITO) o si Alucina con "Oh, qué pulcra Clean Architecture" (FRACASO LETAL).

## 2. Métricas Funcionales Reales
*   Precisión en la radiografía inicial (Mide Tooling `Specfy`).
*   Rate % de Relevancia y Exclusión Mágica del Graph Crawler para recortar el ruido al LLM (Mide `Arch_Context_Builder`).
*   Utilidad Operativa en Recomendaciones (Si la refactorización recomendada te obliga a cambiar 400 ficheros paralelos por algo simple, es baja utilidad).
*   Rate Ratio -> Cost USD / Segundos Demostrado por Job.

## 3. Topología de Principios Filosóficos
Los Cimientos Mandatorios y Constitución Legal de Desarrollo durante todo el camino a seguir, inmutables para Agentes o programadores humanos del sistema:

*   **Tolerar la Ambigüedad:** Si no ves la arquitectura limpia, devuelve `"UNKNOWN"` o `"Spaguetti"`. Miente solo bajo tortura. Diferencia siempre (y con flag específica si es posible en metadata del Context Writer) lo que se detectó de forma Determinista por el compilador Py vs Lo interpretado o deducido holísticamente por el LLM estadístico.
*   **Agnósticidad y Zero Boilers:** No diseñar CodeReborn para arrancar perfecto "en la Demo". Debe soportar golpes feos de directorios insoportables, fallas estúpidas en código sin try/catch. Debe omitir fallas de parsel del binario Go-lint en el subproceso, continuar sin ello y no desplomar al orquestador entero por un simple Exception que rompa la Promesa asíncrona.
*   **Economy Driven:** Todo sacrificio entre tener más contexto del usuario vs abaratar la Query vía resúmenes pre-computados (Chunks RAG), debe resolverse en abaratar. Un Job jamás debe quemar la tarjeta comercial asignada a API LLM Provider Key.
