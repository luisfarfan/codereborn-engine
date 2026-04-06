# Agent — Universal Signal Extractor

> Universal multi-layer code parser and semantic signal extractor.

## Overview
The **Universal Signal Extractor** is the **third agent** in the CodeReborn pipeline, following the Pattern Detector. It acts as the bridge between raw source code and high-level architectural understanding. Instead of relying on a single parsing strategy or massive LLM context windows, it dynamically chooses the most efficient extraction strategy *per file* to harvest structural signals (imports, class definitions, decorators, functions).

## Phased Implementation Status

### FASE 1 (MVP) - ✅ COMPLETED
*   **Layer 1 (Tree-sitter)**: Deterministic AST parsing fully enabled for **Python, JavaScript, and TypeScript** using a centralized `GrammarRegistry` and `.scm` queries. ($0 cost, 100% precision, extremely fast).
*   **Layer 3 (LLM Zero-Shot Fallback)**: Functional universal fallback via **LiteLLM** and **OpenRouter** (initially using `google/gemini-2.0-flash-lite-001`).
*   **Intelligence-Aware Budgeting**: Integrated with `openrouter-insights` to dynamically select models based on real-world capabilities and job-specific spending limits.

### FASE 2 (In Progress)
*   Deploy Tree-sitter grammars for more languages (Go, Rust, Java, etc.) via `.scm` expansion.
*   Implement advanced contextual batching and sampling for the LLM fallback to further optimize costs.

### FASE 3 (Planned)
*   **Layer 2 (LSP)**: Language Server Protocol integration for Deep Semantic mapping in Premium Tiers.
*   **Layer 4 (Pattern Mining)**: AI-generated Regex generation for budget-friendly custom DSL parsing.

## Role in Pipeline
*   **Prerequisites**: Receives `StackIntelligenceReport` (file inventory) and `PatternReport` (sampling rules).
*   **Task**: Selects files based on sampling strategy, performs recursive discovery, auto-detects language, selects the optimal Extraction Layer (Tree-sitter or LLM Fallback), and normalizes the signals.
*   **Consumer**: Outputs a `SignalExtractionReport` used by the **System Mapper** and **DocWriter** for architectural reasoning.

## The Universal Format Guarantee
Regardless of the extraction layer used, the output per file is strictly normalized to the following signal buckets:
*   `imports`
*   `classes`
*   `functions`
*   `methods`
*   `interfaces`
*   `types`
*   `exports`
*   `decorators`
*   `file_dependencies`

## Budgeting & Costs
The agent is **budget-first**. It interacts with `LLMBudgetService` to:
1.  Open a tracking job.
2.  Consult "model insights" (cost/intelligence) via `openrouter-insights`.
3.  Fallback to LLM only if the deterministic Layer 1 (Tree-sitter) lacks a signal query or fails to extract data.
4.  Persist total `spent_usd` in the final report metadata.

## Expected Output
Persists a `SignalExtractionReport` encompassing:
*   `extraction_summary`: Counts per language and per strategy (tree-sitter vs. llm).
*   `signals_by_file`: The normalized JSON mapping of signals.
*   `cost_breakdown`: Explicit mapping of LLM expenditures.
*   `analysis_metadata`: Timestamps, agent version, and analysis duration.
