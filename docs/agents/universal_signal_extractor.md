# Agent — Universal Signal Extractor

> Universal multi-layer code parser and semantic signal extractor.

## Overview
The **Universal Signal Extractor** is the **third agent** in the CodeReborn pipeline, following the Pattern Detector. It acts as the bridge between raw source code and high-level architectural understanding. Instead of relying on a single parsing strategy or massive LLM context windows, it dynamically chooses the most efficient extraction strategy *per file* to harvest structural signals (imports, class definitions, decorators, functions).

## Phased Implementation Roadmap
Given the complexity of universal extraction, this module is developed in strictly delimited phases.

### FASE 1 (MVP) - *Current Target*
*   **Layer 1 (Tree-sitter)**: Deterministic AST parsing enabled initially for **Python, JavaScript, and TypeScript**. ($0 cost, 100% precision, extremely fast).
*   **Layer 3 (LLM Zero-Shot Fallback)**: Acts as the universal fallback for languages lacking a tree-sitter grammar in this phase (e.g., Ruby, Go, Elixir). Uses `LLMBudgetService` for batch processing.
*   *(Note: Layers 2 and 4 are skipped in Phase 1).*

### FASE 2 (Optimization)
*   Deploy Tree-sitter grammars for more languages (Go, Rust, Java, etc.).
*   Implement advanced contextual batching and sampling for the LLM fallback to massively drop costs.

### FASE 3 (Full Scope)
*   **Layer 2 (LSP)**: Language Server Protocol integration for Deep Semantic mapping in Premium Tiers.
*   **Layer 4 (Pattern Mining)**: AI-generated Regex generation for budget-friendly custom DSL parsing.

## Role in Pipeline
*   **Prerequisites**: Receives the `StackReport` (file inventory by language) and the `PatternReport` (which dictates the precise `SamplingStrategy`).
*   **Task**: Selects files dictated by the sampling strategy, auto-detects language, selects the optimal Extraction Layer (Tree-sitter or LLM), and normalizes the output.
*   **Consumer**: Outputs a `SignalExtractionReport` that allows the subsequent Architectural Inductor (or System Mapper) agent to reason without directly reading massive source code payloads.

## The Universal Format Guarantee
No matter if the agent used Deterministic AST (Tree-sitter) or Generative AI (Layer 3), the output per file is STRICTLY normalized to:
*   `imports`
*   `class_declarations` (including base classes)
*   `function_declarations` (including export visibility)
*   `decorators`
*   `type_definitions`
*   `file_dependencies`

## Expected Output
Persists a `SignalExtractionReport` encompassing `extraction_summary`, `signals_by_file`, `global_patterns`, and an explicit `cost_breakdown` mapping how much was spent on LLM fallbacks.
