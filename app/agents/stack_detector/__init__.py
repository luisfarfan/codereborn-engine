"""
StackDetector agent.

Responsibility: Detect the technology stack of a repository using
specfy/stack-analyser (static analysis, zero LLM cost) and enrich
the result with an LLM-powered confidence evaluation.

Outputs: StackIntelligenceReport → stored in stack_reports table.
"""
