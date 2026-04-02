# Componente 5: Doc Writing Layer (El Multi-Pool Asíncrono)

Para eludir bloqueos masivos y pérdida absoluta de coherencia estilística o sesgos tonales en Foundational Models al emitir outputs inmensos ("Dime qué hace la API en un tono muy detallado e hiper-técnico, ah, y abajo redactame un cuentito para enseñar a mis juniors a arrancar, y ahora dame un json súper riguroso de convenciones de boundaries... todo en el mismo prompt!!"), **CodeReborn implementa una estrategia de Delegación Segregada Multi-Agente.**

El componente `doc_writing_layer` no es *UN* agente, es en realidad el bloque final en CrewAI configurado como un *Branch Paralelo* de Pool de Generación. Consta de **4 Agentes Writters independientes**. 

Toman como variables inyectables todos los Context JSONs persistidos de los Componentes previos simultáneamente (El Architecture, El System y El Debt Summary). Los asimilan y se limitan a "Extraer la prosa".

*Importante:* Consultan invariablemente al Budget antes de inyectar su Prompt a `LiteLLM`. Sus roles preferencialmente deberían ser asumidos por modelos `Tier 2` (Rápidos, económicos, perfil redactor narrativo - Ej. Claude Haiku, GPT-4o-mini).

## Writer 1: Technical Doc Writer
*Audiencia Target:* Ingenieros de Sistemas Senior que requieren meter mano ya. Perfiles Técnicos estrictos (SRE, Lead Devs).
*Redacción exigida:* Zero ambigüedad. Enfocado en describir la topología expuesta del frente, convención técnica detectada para que mantengan la concordancia, guía de navegación abstracta a bajo nivel de funciones de entrada y librerías externas que orquestan el código. Data Flows.

## Writer 2: Human Doc Writer
*Audiencia Target:* Onboarding de programadores Junior, Project Managers Técnicos, stakeholders de negocio.
*Redacción exigida:* Altamente amigable y secuencial "Paso a Paso". El "Cuentito". Fomenta un glosario, listado de FAQs proyectados y guía blanda de cómo iniciar la app en local inferida por el pipeline.

## Writer 3: AI Context Writer (Extremadamente Crítico)
*Audiencia Target:* Motores Vectoriales, Asistentes de IA de terceros (Cursor, OpenUI, Chatbots de la propia empresa RAG).
*Redacción exigida:* Debe prohibirse narrar de forma humana en el formato output. Es imperativo forzar el LLM Pydantic JSON output strict flag (Function Calling / Structured Outputs) hacia un Schema fuertemente tipado. 
```json
{
  "facts": ["Es repo Express JS"],
  "rules": ["Ningun controler usa async_wrapper, todos inyectan try-catch inline"],
  "boundaries": ["Nunca invocar el Service Auth0 fuera del folder /shared/auth"],
  "extension_points": ["Seguro meter Workers en /src/jobs ya que procesan independiente."],
}
```

## Writer 4: Debt Doc Writer
*Audiencia Target:* Engineering Managers, Product Owners.
*Redacción exigida:* Visibilidad extrema y dramática. Sintetizar el "Tech Debt Analysis Report". En vez de 4.000 fallas locales de linting, devolver un Executive Summary Markdown enfocado a un Roadmap Táctico Sugerido de curación. Riesgos estructurales detectados y trade-offs entre dejarlos o arreglarlos.

## Output y Almacenamiento Centralizado
Finalizan emitiendo 4 artefactos distintos a PostgreSQL sobre la tabla masiva de texto `doc_artifacts`. Guardan el timestamp, formato Markdown/Json, y el Job Id unificado. Completado esto se da Cierre de Estado Formal al Pipeline central (Termina el CrewAI) procediendo al broadcast final de tarea terminada.
