"""
GrammarRegistry - Dynamic management of Tree-sitter grammars.
Follows the universal extraction principle: Loads grammars on-demand
without hardcoded imports per language.
"""

import os
import logging
import importlib
from typing import Any, Dict, Optional
from tree_sitter import Language, Parser, Query

logger = logging.getLogger(__name__)

class GrammarRegistry:
    """
    Registry for Tree-sitter languages that loads grammars dynamically.
    Enables supporting hundreds of languages through 'tree-sitter-<lang>' packages.
    """

    def __init__(self, grammars_dir: str):
        self.grammars_dir = os.path.abspath(grammars_dir)
        logger.info(f"GrammarRegistry initialized with grammars_dir: {self.grammars_dir}")
        self.languages: Dict[str, Language] = {}
        self.queries: Dict[str, Query] = {}
        self.parsers: Dict[str, Parser] = {}

    def has_grammar(self, language_name: str) -> bool:
        """Checks if a Tree-sitter grammar is available for the language."""
        if language_name in self.languages:
            return True
        
        # Strategy: attempt dynamic import of the standard package name
        # Modern Tree-sitter packages follow naming: tree-sitter-<lang>
        try:
            # Replace '-' with '_' for python package names
            pkg_name = f"tree_sitter_{language_name.replace('-', '_')}"
            module = importlib.import_module(pkg_name)
            
            # Standard entry point for new tree-sitter packages is language()
            lang_obj = module.language()
            self._register_language(language_name, lang_obj)
            return True
        except (ImportError, AttributeError, Exception):
            # Fallback for complex names (like typescript-typescript)
            if language_name == "typescript":
                try:
                    import tree_sitter_typescript
                    lang_obj = tree_sitter_typescript.language_typescript()
                    self._register_language(language_name, lang_obj)
                    return True
                except ImportError:
                    pass
            return False

    def _register_language(self, name: str, language_obj: Any):
        """Standardized registration of a dynamically loaded language."""
        lang = Language(language_obj)
        self.languages[name] = lang
        
        # Load associated .scm query file if exists
        query_path = os.path.join(self.grammars_dir, f"{name}.scm")
        if os.path.exists(query_path):
            logger.info(f"Found signal query file at {query_path}")
            try:
                with open(query_path, "r") as f:
                    query_scm = f.read()
                self.queries[name] = Query(lang, query_scm)
                logger.info(f"Successfully loaded signal query for '{name}'")
            except Exception as e:
                logger.error(f"Failed to load query for {name} from {query_path}: {e}")
        else:
            logger.warning(f"Query file NOT FOUND for {name} at {query_path}")

    def get_parser(self, language_name: str) -> Optional[Parser]:
        """Returns a configured parser for the given language."""
        if not self.has_grammar(language_name):
            return None
        
        if language_name not in self.parsers:
            parser = Parser(self.languages[language_name])
            self.parsers[language_name] = parser
        
        return self.parsers[language_name]

    def get_query(self, language_name: str) -> Optional[Query]:
        """Returns the pre-compiled query for the language."""
        return self.queries.get(language_name)

    # Comprehensive mapping of extensions to Tree-sitter language names
    # This is the single source of truth for supported file types.
    EXTENSION_MAPPING = {
        ".py": "python",
        ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
        ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript", ".cts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp", ".c": "c", ".hpp": "cpp", ".cc": "cpp", ".h": "cpp",
        ".java": "java",
        ".kt": "kotlin", ".kts": "kotlin",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "bash", ".bash": "bash", ".zsh": "bash",
        ".sql": "sql",
        ".prisma": "prisma",
        ".proto": "protobuf",
        ".yaml": "yaml", ".yml": "yaml",
        ".json": "json",
        ".md": "markdown"
    }

    def resolve_language(self, file_path: str) -> Optional[str]:
        """Determines the canonical language name from a file path."""
        _, ext = os.path.splitext(file_path)
        return self.resolve_language_by_extension(ext)

    def resolve_language_by_extension(self, extension: str) -> Optional[str]:
        """Determines the canonical language name from an extension."""
        return self.EXTENSION_MAPPING.get(extension.lower())

    def get_supported_extensions(self) -> list[str]:
        """Returns a list of all file extensions that this registry can potentially handle."""
        return list(self.EXTENSION_MAPPING.keys())
