# Componente 3: System Mapper (El Core Analítico)

Es **Agente 3**, y el primer gran Orquestador Analítico/Cognitivo basado 100% en LLMs (crewai.Agent puro), que infiere, consolida y juzga la arquitectura de la organización basándose sistemáticamente en la inferencia estática anterior (el Payload).

## Pre-Condición Obligatoria (Gatekeeping)
Dada la ingesta enorme de Context JSON que acarrea este Agente, la *primera orden* de su Task será obligatoriamente someter el tamaño tokenizado estimado de su petición en espera hacia el utilitario central `LLMBudgetService`.

Este Gatekeeper calculará si esto le cuesta X dólares al Job y decidirá (ver `/docs/03_pipeline_and_budget_service.md`).
Dependiendo el resultado que devuelva el presupuesto, el SystemMapper muta radicalmente su lógica de llamado interno hacia `LiteLLM`:

*   **Si es Single-Pass:** El `SystemMapper` envía de un plumazo todo el JSON Payload generado por el `Architecture Builder`, pidiéndole al LLM descifrar integralmente el dominio.
*   **Si es Multi-Zone (Acomodación Iterativa):** El Agente entra en iterador de Python (for loop). Corta mentalmente las "Zonas" (carpetas gigantes). Emite un Prompt por API Request *independiente* para el backend de usuarios, otro Prompt api request para la carpeta pagos `pay/`, y un último mega-prompt que engulle los 2 resúmenes generados para pedirle al LLM el veredicto arquitectónico global final cruzado entre ambas piezas.

## Filosofía Interpretativa (Scope-Awareness)
No puede fallar usando patrones agnósticos erróneos. El `System Mapper` adapta lo que vigila de acuerdo al `analysis_scope` del Job dictaminado:

1.  **Si scope es Frontend:** El LLM evalúa específicamente: Server State vs Local State (Redux/Mobx/Context), enrutamientos (pages, layouts, SSR signals), componentes compartidos de UI Library.
2.  **Si scope es Backend:** Evalúa límites DDD de Módulos Funcionales, cruce de Hexagonal Ports, boundaries entre repositorios transaccionales vs endpoints tontos, uso de event-buses.
3.  **Si scope es Mobile:** Evalúa navegación local, pantallas, y persistencia local asíncrona tipo AsyncStorage.

## Respuestas Exigidas al LLM (El Output Cognitivo Real)
El prompt que consume modelo mayor (`GPT-4o/Claude 3.5 Sonnet` - modelo tier 1) exige no ser benevolente ni condescendiente con la arquitectura. Debe tolerar repos legacy horrendos.
Responde cuestiones como: ¿Por qué hay mezcla de estilos (Arquitectura Evolutiva)? ¿Se ven trazos de refactor incompletos asumiendo un MVC roto? ¿Están los boundaries bien cortados o vemos Spaguetti transaccional?

## Output Target: System Map Report
Persiste este Json dict a PostgreSQL a la tabla `system_maps`. 

Manda a guardar:
*   `dominant_architecture`: String (ej. "hexagonal_partial", "spaguetti").
*   `system_style`: Redacción sintética (Texto puro).
*   `patterns_detected`: Estructurales.
*   `layers_detected`: Detección clara de dónde arranca el application_layer.
*   `boundaries`: Mapas de fronteras lógicas.
*   `evolution_signals`: Rastros de código obsoleto.
*   `confidence_score`: Nivel de convicción de las respuestas dadas (Float).
