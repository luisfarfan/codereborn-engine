# Agent — Pattern Detector

> Universal Architecural Interpretation (Successor to Architecture Context Builder)

## Overview
The **Pattern Detector** agent interprets the repository's technology stack and file distribution into high-level architectural patterns. Unlike its predecessor, it does not rely on language-specific regex rules; instead, it uses LLM-driven reasoning to identify structure across any programming language.

## Role in Pipeline
*   **Fase 1 (Prerequisite)**: Receives the `StackReport` from the **Stack Detector**.
*   **Fase 2 (Current)**: Analyzes facts like folder names, file counts, and framework usage to induce architectural intent.
*   **Fase 3 (Consumer)**: Provides the `SamplingStrategy` that tells the **Universal Signal Extractor** which files are most valuable to analyze.

## Core Responsibilities
1.  **Pattern Induction**: Categorizes the repository into patterns (e.g., Layered, Hexagonal, MVC, Monolithic, etc.).
2.  **Directory Interpretation**: Assigns architectural roles to top-level folders (e.g., `app/api` is the "Presentation Layer").
3.  **Sampling Strategy**: Recommends a subset of files to analyze to maximize architectural understanding while minimizing LLM costs.
4.  **Framework Convention Mapping**: Identifies specific conventions (e.g., "FastAPI Router structure", "Next.js Pages directory").

## Technical Specs
*   **LLM Driven**: Uses `google/gemini-2.0-flash-lite` (via OpenRouter) to handle large context windows of file trees.
*   **Budget Managed**: Must pass through `LLMBudgetService` for approval before execution.
*   **Output**: `PatternReport` (Structured JSON).

## Success Metrics
*   **Precision (Pattern)**: > 90% accuracy on standard frameworks.
*   **Efficiency**: Average interpretation cost < $0.005 USD.
*   **Stability**: Zero validation errors on returned Pydantic models.
