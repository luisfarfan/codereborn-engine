# Guía de Integración del Frontend con CodeReborn MCP

Esta guía describe cómo conectar una aplicación frontend al servidor MCP (Model Context Protocol) de CodeReborn.

## 1. Instalación del SDK

El frontend debe usar el SDK oficial de MCP para JavaScript/TypeScript.

```bash
npm install @modelcontextprotocol/sdk
```

## 2. Configuración del Cliente (SSE)

Dado que las herramientas del MCP están expuestas por el servidor FastAPI en el mismo puerto, utilizaremos el transporte **SSE (Server-Sent Events)**.

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

async function connectToMCP() {
  // 1. Crear el transporte apuntando al endpoint de la API
  const transport = new SSEClientTransport(
    new URL("http://localhost:8000/mcp/sse")
  );

  // 2. Crear y conectar el cliente
  const client = new Client(
    {
      name: "CodeReborn-Frontend",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  await client.connect(transport);
  console.log("Conectado al MCP de CodeReborn");
  
  return client;
}
```

## 3. Uso de las Herramientas

Una vez conectado, puedes listar y ejecutar las herramientas disponibles para entender el sistema:

```typescript
// Listar herramientas
const tools = await client.listTools();
console.log("Herramientas disponibles:", tools);

// Obtener overview del sistema
const overview = await client.callTool({
  name: "get_system_overview",
  arguments: {}
});
console.log("System Overview:", overview.content[0].text);
```

## Herramientas Disponibles

- `get_system_overview`: Visión general, stack core y reglas del sistema.
- `get_api_contracts`: Documentación completa de los contratos REST de la API.
- `get_data_contracts`: Esquemas Pydantic para outputs de agentes.
- `get_agent_specs`: Especificaciones de roles y tareas de cada agente (StackDetector, etc.).
- `get_implementation_map`: Mapeo entre especificaciones y archivos `.py` reales.

## Seguridad

Si la API principal requiere autenticación, el transporte SSE adjuntará automáticamente las cookies si están configuradas, o puedes pasar el token en la URL si es necesario (dependiendo de la configuración de CORS en el backend).

---

> [!TIP]
> Si el frontend tiene un chat con IA embebido, puedes pasarle este cliente MCP para que la IA pueda explorar la arquitectura del proyecto CodeReborn de forma autónoma.
