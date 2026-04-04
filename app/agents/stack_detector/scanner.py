import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from app.domain.enums import AnalysisScope
from app.models.stack_models import (
    FileInventory,
    LanguageFileBreakdown,
    DirectoryNode,
    DirectoryStructure,
    RepositoryMetadata
)

logger = logging.getLogger(__name__)

class RepoScanner:
    """
    Deterministic filesystem scanner for CodeReborn.
    Generates File Inventory, Directory Structure, and Metadata without LLM.
    """

    # Common noise to exclude
    ALWAYS_EXCLUDE_DIRS = {
        "node_modules", "vendor", "packages", ".git", ".svn", ".hg",
        "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv",
        "dist", "build", "target", "out", "bin", "obj"
    }

    # Conditional exclusion patterns based on scope
    FRONTEND_PATTERNS = {"public", "static", "assets", "components", "pages", "views"}
    BACKEND_PATTERNS = {"migrations", "models", "repositories", "controllers", "services", "api"}

    def __init__(self, repo_path: str, analysis_scope: AnalysisScope = AnalysisScope.ALL):
        self.repo_path = Path(repo_path).resolve()
        self.scope = analysis_scope
        self.inventory = FileInventory()
        self.structure = DirectoryStructure()
        self.metadata = RepositoryMetadata()
        
        # Internal tracking
        self.dir_map: Dict[str, DirectoryNode] = {}
        self.max_depth = 0
        self.file_count_by_depth: Dict[int, int] = {}

    def scan(self) -> Dict[str, Any]:
        """
        Performs the full recursive scan of the repository.
        """
        start_time = datetime.now()
        
        # 1. Check for Git availability and basic metadata
        self.metadata.git_available = (self.repo_path / ".git").exists()
        
        # 2. Main Walk
        self._walk()

        # 3. Finalize Statistics
        self.metadata.total_size_bytes = self._get_total_size()
        self.metadata.file_count_by_depth = {str(k): v for k, v in self.file_count_by_depth.items()}
        
        # 4. Finalize Structure statistics
        self._finalize_structure()

        return {
            "file_inventory": self.inventory,
            "directory_structure": self.structure,
            "repository_metadata": self.metadata
        }

    def _walk(self):
        root_str = str(self.repo_path)
        
        for root, dirs, files in os.walk(root_str):
            rel_root = os.path.relpath(root, root_str)
            if rel_root == ".":
                rel_root = ""

            # Calculate depth
            depth = 0 if not rel_root else len(Path(rel_root).parts)
            self.max_depth = max(self.max_depth, depth + 1)

            # Apply Exclusions to 'dirs' in-place (modifies os.walk traversal)
            dirs[:] = [d for d in dirs if self._should_include_dir(d, rel_root)]
            
            # Record exclusion of directories for statistics
            # (Note: In a pure deterministic scan, we track file counts primarily)

            # Process Files
            dir_node = DirectoryNode(
                path=rel_root or "/",
                name=Path(root).name if rel_root else "root",
                depth=depth + 1,
                parent=str(Path(rel_root).parent) if depth > 0 else None,
                subdirectories=dirs.copy()
            )

            for f in files:
                if self._is_binary_or_hidden(f):
                    self.inventory.excluded_files += 1
                    self.inventory.exclusion_reasons["binary_files" if not f.startswith(".") else "hidden_files"] += 1
                    continue

                f_path = Path(rel_root) / f
                f_ext = f_path.suffix.lower().lstrip(".")
                lang = self._map_extension_to_language(f_ext)
                
                # Update inventory
                self._update_inventory(str(f_path), f, lang)
                
                # Update directory node
                dir_node.file_count += 1
                dir_node.file_breakdown[lang] = dir_node.file_breakdown.get(lang, 0) + 1
                
                # Update depth stats
                d_level = depth + 1
                self.file_count_by_depth[d_level] = self.file_count_by_depth.get(d_level, 0) + 1

            if dir_node.file_count > 0 or dir_node.subdirectories:
                 self.dir_map[dir_node.path] = dir_node

    def _should_include_dir(self, name: str, rel_parent: str) -> bool:
        if name in self.ALWAYS_EXCLUDE_DIRS or name.startswith("."):
            return False
            
        # Scope-based exclusions
        if self.scope == AnalysisScope.BACKEND:
             if name in self.FRONTEND_PATTERNS:
                 return False
        elif self.scope == AnalysisScope.FRONTEND:
             if name in self.BACKEND_PATTERNS:
                 return False
                 
        return True

    def _is_binary_or_hidden(self, filename: str) -> bool:
        if filename.startswith("."):
            return True
        binary_extensions = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".pyc"}
        return Path(filename).suffix.lower() in binary_extensions

    def _map_extension_to_language(self, ext: str) -> str:
        mapping = {
            "py": "python", "js": "javascript", "ts": "typescript", "tsx": "typescript", "jsx": "javascript",
            "go": "go", "rs": "rust", "java": "java", "cs": "csharp", "cpp": "cpp", "c": "c",
            "rb": "ruby", "php": "php", "sh": "shell", "md": "markdown", "json": "json",
            "yaml": "yaml", "yml": "yaml", "toml": "toml", "html": "html", "css": "css"
        }
        return mapping.get(ext, "other")

    def _update_inventory(self, rel_path: str, name: str, lang: str):
        if lang not in self.inventory.by_language:
            self.inventory.by_language[lang] = LanguageFileBreakdown()
        
        breakdown = self.inventory.by_language[lang]
        
        # Categorize by Type
        is_test = self._is_test_file(rel_path, name)
        is_config = self._is_config_file(name)
        is_doc = self._is_doc_file(rel_path, name)

        if is_test:
            breakdown.test_files.append(rel_path)
            self.inventory.by_type["tests"] += 1
        elif is_config:
            self.inventory.by_type["configs"] += 1
        elif is_doc:
            self.inventory.by_type["docs"] += 1
        else:
            breakdown.code_files.append(rel_path)
            self.inventory.by_type["code"] += 1
        
        breakdown.total_files += 1
        self.inventory.total_files += 1

    def _is_test_file(self, path: str, name: str) -> bool:
        test_patterns = ["/test/", "/tests/", "/__tests__/", "/spec/"]
        name_patterns = [r"^test_.*\.py$", r".*_test\.go$", r".*\.test\.(js|ts)$", r".*\.spec\.(js|ts)$"]
        
        if any(p in path for p in test_patterns):
            return True
        if any(re.match(p, name) for p in name_patterns):
            return True
        return False

    def _is_config_file(self, name: str) -> bool:
        config_exts = {".json", ".yaml", ".yml", ".toml", ".ini", ".conf"}
        config_names = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Makefile"}
        return Path(name).suffix.lower() in config_exts or name in config_names

    def _is_doc_file(self, path: str, name: str) -> bool:
        if name.lower().endswith(".md") or name.lower().endswith(".rst"):
            return True
        if "docs/" in path:
            return True
        return False

    def _get_total_size(self) -> int:
        total = 0
        try:
            for f in self.repo_path.rglob('*'):
                if f.is_file():
                    total += f.stat().st_size
        except Exception:
            pass
        return total

    def _finalize_structure(self):
        # We only return the first 4-5 levels in root_directories list to keep payload manageable
        self.structure.root_directories = [
            node for node in self.dir_map.values() if node.depth <= 5
        ]
        
        self.structure.statistics["total_directories"] = len(self.dir_map)
        self.structure.statistics["max_depth"] = self.max_depth
        
        # Largest directory
        if self.dir_map:
            largest = max(self.dir_map.values(), key=lambda x: x.file_count)
            self.structure.statistics["largest_directory"] = {
                "path": largest.path,
                "file_count": largest.file_count
            }
