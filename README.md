# 🚀 CodeReborn Engine

> **Breathe life into legacy codebases.**  
> CodeReborn Engine transforms messy, old repositories into structured, indexable intelligence using a deterministic + LLM hybrid pipeline.

---

## 🛠️ StackDetector Demo

The **StackDetector** is the first agent in our pipeline. It is **100% deterministic** and high-fidelity, designed to identify the technology DNA of any repository without costing a single LLM token.

### 📋 Prerequisites

1. **Python 3.11+** installed.
2. **Node.js & npm** installed (required for `@specfy/stack-analyser`).
3. **Docker Desktop** (to run PostgreSQL & Redis).

### ⚡ Quick Start

1. **Setup & Dependencies**
   ```bash
   make setup
   ```

2. **Start Infrastructure**
   ```bash
   make infra-up
   ```

3. **Run the Demo** (Analyze this project)
   ```bash
   make demo
   ```

---

## 🔍 Custom Analysis

You can analyze **any folder** on your computer by passing its absolute path to the `make analyze` command.

### Standard Output
```bash
make analyze PATH_TO_ANALYZE=/Users/lucho/projects/my-legacy-app
```

### JSON Output (Machine Readable)
```bash
make analyze PATH_TO_ANALYZE=. JSON=true
```

---

## 🧠 Behind the Scenes

When you run the StackDetector:
1. **Extraction**: We wrap `@specfy/stack-analyser` (Node.js) to perform a brute-force heuristic search for languages and frameworks.
2. **Post-Processing**: Our Python engine normalizes the raw tool data, infers the analysis scope (Frontend, Backend, etc.), and calculates a confidence score.
3. **Persistence**: The findings are stored in **PostgreSQL** (`stack_reports` table) via **SQLModel** for later use by the next agents in the pipeline.

---

## 🏗️ Project Architecture

CodeReborn follows **Clean Architecture** principles:
- **`app/agents/`**: Pure orchestration logic for AI agents.
- **`app/models/`**: SQLModel database models and Pydantic domain schemas.
- **`app/infrastructure/`**: Database connections, Redis, and external tools.
- **`app/domain/`**: Enums and shared domain logic.

---

## 📡 Pipeline Status

| Agent | Status | Type | Description |
|-------|--------|------|-------------|
| **StackDetector** | ✅ Ready | Deterministic | Framework, service, and language discovery. |
| **ContextBuilder** | 🏗️ Next | Deterministic | Recursive tree crawler and zone identification. |
| **SystemMapper** | ⏳ Planned | LLM | High-level architecture mapping. |
| **DebtAnalyzer** | ⏳ Planned | Hybrid | Technical debt and anti-pattern detection. |
| **DocWriter** | ⏳ Planned | LLM | Multidimensional documentation synthesis. |

---

*Made with ❤️ by CodeReborn Team*
