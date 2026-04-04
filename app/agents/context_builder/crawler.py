import os
import logging
from pathlib import Path
from typing import Set, List, Dict, Any

logger = logging.getLogger(__name__)

# Default directories to ignore for architectural context
DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".astro",
    "target",  # Rust/Java
    "obj",     # .NET
    "bin",     # .NET
    "storage", # Laravel/Engine temp
    "tmp",
}

DEFAULT_IGNORE_FILES = {
    ".DS_Store",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "composer.lock",
    "Cargo.lock",
    "go.sum",
}

class RepoCrawler:
    """
    Deterministic repository walker that identifies interesting files 
    for architectural analysis.
    """

    def __init__(self, root_path: str, custom_ignore: Set[str] = None):
        self.root_path = Path(root_path).resolve()
        self.ignore_dirs = DEFAULT_IGNORE_DIRS.copy()
        if custom_ignore:
            self.ignore_dirs.update(custom_ignore)
        
        self.ignore_files = DEFAULT_IGNORE_FILES

    def crawl(self) -> Dict[str, Any]:
        """
        Walks the repository and builds a summary.
        Returns: {
            "files": List[Path],
            "directory_summaries": List[Dict],
            "total_size_bytes": int
        }
        """
        all_files = []
        dir_summaries = []
        total_size = 0

        for root, dirs, files in os.walk(self.root_path):
            rel_root = Path(root).relative_to(self.root_path)
            
            # Prune ignored directories in-place to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs and not d.startswith(".")]

            # Summarize current directory
            current_dir_files = []
            extensions = {}
            
            for f in files:
                if f in self.ignore_files or f.startswith("."):
                    continue
                
                f_path = Path(root) / f
                try:
                    f_size = f_path.stat().st_size
                    total_size += f_size
                    
                    rel_path = f_path.relative_to(self.root_path)
                    all_files.append(rel_path)
                    current_dir_files.append(str(rel_path))
                    
                    ext = f_path.suffix.lower() or "no-ext"
                    extensions[ext] = extensions.get(ext, 0) + 1
                    
                except OSError:
                    continue

            if current_dir_files:
                dir_summaries.append({
                    "dir_path": str(rel_root) if str(rel_root) != "." else "/",
                    "file_count": len(current_dir_files),
                    "predominant_types": sorted(extensions.keys(), key=lambda x: extensions[x], reverse=True)[:3],
                })

        return {
            "files": all_files,
            "directory_summaries": dir_summaries,
            "total_size_bytes": total_size
        }
