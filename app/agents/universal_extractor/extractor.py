"""
SignalExtractor - Scalable AST extraction using Tree-sitter.
Follows Layer 1 specifications: Extract signals universally.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from tree_sitter import QueryCursor

from app.agents.universal_extractor.registry import GrammarRegistry
from app.models.stack_models import UniversalSignalFormat, SignalDeclaration

logger = logging.getLogger(__name__)

class SignalExtractor:
    """
    Engine for extracting architectural signals from source code using Tree-sitter.
    Standardizes capture tags from .scm files into UniversalSignalFormat.
    """

    def __init__(self, registry: GrammarRegistry):
        self.registry = registry
        # Maps capture tags from .scm to the corresponding signal bucket
        self.TAG_MAP = {
            "import": "imports",
            "class": "classes",
            "func": "functions",
            "method": "methods",
            "decorator": "decorators",
            "interface": "interfaces",
            "type": "types",
            "export": "exports"
        }

    async def extract_from_file(self, file_path: str, repo_path: str) -> Optional[UniversalSignalFormat]:
        """Extracts signals using pre-compiled queries and tag mapping."""
        
        language_name = self.registry.resolve_language(file_path)
        if not language_name:
            return None
            
        # Ensure grammar and query are loaded (has_grammar triggers dynamic loading)
        if not self.registry.has_grammar(language_name):
            return None
            
        query = self.registry.get_query(language_name)
        parser = self.registry.get_parser(language_name)
        
        if not query:
            logger.warning(f"No signal query (.scm) found for language '{language_name}'")
            # We continue to Layer 3 if query is missing
            return None
            
        if not parser:
            logger.warning(f"No parser available for language '{language_name}'")
            return None

        full_path = os.path.join(repo_path, file_path)
        if not os.path.exists(full_path):
            logger.warning(f"File not found: {full_path}")
            return None

        try:
            with open(full_path, "rb") as f:
                content = f.read()

            tree = parser.parse(content)
            
            # Use QueryCursor for 0.24+ compatibility
            cursor = QueryCursor(query)
            raw_captures = cursor.captures(tree.root_node)
            
            # Reconstruct legacy flattened format: list of (node, tag)
            captures = []
            for tag, nodes in raw_captures.items():
                for node in nodes:
                    captures.append((node, tag))

            # Initialize all possible buckets from TAG_MAP
            signals_data = {bucket: [] for bucket in self.TAG_MAP.values()}
            signals_data["file_dependencies"] = [] # Extra legacy field

            # Process captures dynamically based on TAG_MAP
            for node, tag in captures:
                bucket = self.TAG_MAP.get(tag)
                if not bucket:
                    continue
                
                text = node.text.decode("utf8")
                line_no = node.start_point[0] + 1
                
                # SignalDeclaration requires a name and optional line_number
                signal = SignalDeclaration(
                    name=text,
                    line_number=line_no,
                    is_exported=True # Tree-sitter L1 usually finds top-level symbols
                )
                signals_data[bucket].append(signal)

            # Deduplicate generic buckets safely (SignalDeclaration is unhashable)
            for key in ["imports", "decorators", "types", "interfaces"]:
                if key not in signals_data:
                    continue
                unique_signals = []
                seen_names = set()
                for sig in signals_data[key]:
                    if sig.name not in seen_names:
                        unique_signals.append(sig)
                        seen_names.add(sig.name)
                signals_data[key] = unique_signals

            # Signal check: if no signals were found in any bucket, we consider extraction failed
            # unless the file is empty, but architecture-wise we want files with signals.
            total_signals = sum(len(v) for v in signals_data.values())
            if total_signals == 0 and len(content) > 10:
                logger.debug(f"No architectural signals found in {file_path}")
                return None

            return UniversalSignalFormat(
                file_path=file_path,
                language=language_name,
                extraction_method="tree-sitter",
                signals=signals_data,
                metadata={
                    "lines_of_code": len(content.splitlines()),
                    "confidence": 1.0,
                    "extraction_timestamp": datetime.utcnow().isoformat(),
                    "signals_detected": total_signals
                }
            )

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}", exc_info=True)
            return None
