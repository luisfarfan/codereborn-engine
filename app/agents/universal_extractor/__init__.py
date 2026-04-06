"""
Universal Signal Extractor Module.
Multi-layer extraction strategy (Tree-sitter, LSP, LLM).
"""

from .agent import UniversalExtractorAgent
from .extractor import SignalExtractor
from .registry import GrammarRegistry
