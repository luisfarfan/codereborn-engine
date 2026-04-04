import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Set

logger = logging.getLogger(__name__)

# Common import patterns across languages
IMPORT_PATTERNS = [
    r"import\s+.*\s+from\s+['\"](.*)['\"]",  # ESM (JS/TS)
    r"import\s+['\"](.*)['\"]",              # ESM (JS/TS) or Go
    r"require\(['\"](.*)['\"]\)",           # CommonJS (JS)
    r"from\s+(.*)\s+import",                 # Python
    r"import\s+(.*)",                        # Python or Go
]

class ArchitecturalRanker:
    """
    Calculates file importance based on Fan-in/Fan-out and tree depth.
    Deterministic — zero LLM tokens.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.scores: Dict[str, float] = {}
        self.imports_by_file: Dict[str, Set[str]] = {}
        self.imported_by_file: Dict[str, Set[str]] = {}

    def analyze_dependencies(self, files: List[Path]):
        """
        Parses imports for all files to build the dependency graph.
        """
        file_paths = {str(fp).lower(): fp for fp in files}
        
        for fp in files:
            full_path = self.root_path / fp
            rel_path_str = str(fp).lower()
            
            if rel_path_str not in self.imports_by_file:
                self.imports_by_file[rel_path_str] = set()
            if rel_path_str not in self.imported_by_file:
                self.imported_by_file[rel_path_str] = set()

            try:
                content = full_path.read_text(errors="ignore", encoding="utf-8")
                
                for pattern in IMPORT_PATTERNS:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        import_str = match.group(1).strip()
                        
                        # Resolve imports (basic heuristic)
                        # We try to find any part of the import_str in our known files
                        import_parts = import_str.split("/")
                        potential_name = import_parts[-1].lower()
                        
                        for path_str in file_paths:
                            # Heuristic: if the import string ends with the filename (without ext)
                            # or matches a significant part of the path
                            if potential_name in path_str and (path_str.endswith(f"{potential_name}.py") or path_str.endswith(f"{potential_name}.ts") or path_str.endswith(f"{potential_name}.js")):
                                self.imports_by_file[rel_path_str].add(path_str)
                                
                                if path_str not in self.imported_by_file:
                                    self.imported_by_file[path_str] = set()
                                self.imported_by_file[path_str].add(rel_path_str)
                                break
                                
            except Exception as e:
                logger.warning(f"Failed to parse imports for {rel_path_str}: {str(e)}")

    def calculate_scores(self, files: List[Path], classifications: Dict[str, Dict]):
        """
        Calculates the value score [0-1] for each file.
        """
        for fp in files:
            rel_path = str(fp).lower()
            score = 0.1 # Base score
            
            # 1. Fan-in (most important signal: how many things use this?)
            fan_in = len(self.imported_by_file.get(rel_path, []))
            score += min(fan_in * 0.1, 0.4) # Max 0.4 from fan-in
            
            # 2. Fan-out (orchestrators)
            fan_out = len(self.imports_by_file.get(rel_path, []))
            score += min(fan_out * 0.05, 0.2) # Max 0.2 from fan-out
            
            # 3. Role-based boost
            cls = classifications.get(str(fp), {})
            role = cls.get("role", "unknown")
            if role in ["main", "controller", "service", "config"]:
                score += 0.2
            elif role == "test":
                score -= 0.1 # Lower priority for tests
            
            # 4. Tree depth boost (shallower files are often more important)
            depth = len(fp.parts)
            score += max(0.1 - (depth * 0.02), 0.0) # Max 0.1 boost for root files
            
            self.scores[str(fp)] = min(score, 1.0)

    def get_rankings(self) -> List[Dict[str, Any]]:
        """
        Returns sorted rankings with reasoning.
        """
        rankings = []
        for fp_str, score in sorted(self.scores.items(), key=lambda x: x[1], reverse=True):
            reasons = []
            if len(self.imported_by_file.get(fp_str.lower(), [])) > 2:
                reasons.append("high_fan_in")
            if len(self.imports_by_file.get(fp_str.lower(), [])) > 5:
                reasons.append("high_fan_out")
            if score > 0.6:
                reasons.append("core_architectural_role")
            
            rankings.append({
                "file_path": fp_str,
                "value_score": round(score, 2),
                "reasons": reasons if reasons else ["structural_presence"]
            })
        return rankings
