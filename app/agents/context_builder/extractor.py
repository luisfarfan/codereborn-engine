import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Any

logger = logging.getLogger(__name__)

class SignalExtractor:
    """
    High-speed regex-based extractor for architectural signals.
    Extracts imports, decorators, and base classes to build a 'Technical DNA' of the repo.
    """

    # Common patterns across languages
    PATTERNS = {
        "python": {
            "import": r"^(?:from|import)\s+([\w\.]+)",
            "decorator": r"^\s*@([\w\.\(]+)",
            "inheritance": r"^class\s+\w+\s*\(([\w\s,]+)\):",
        },
        "javascript": {
            "import": r"import\s+.*?\s+from\s+['\"](.*?)['\"]",
            "decorator": r"@([\w\.]+)",
            "interface": r"interface\s+\w+\s+extends\s+([\w\s,]+)",
            "class_extends": r"class\s+\w+\s+extends\s+([\w\s,]+)",
        },
        "java_csharp": {
            "annotation": r"@([\w\.\(]+)",
            "inheritance": r"class\s+\w+\s+(?:extends|implements|:)\s+([\w\s,<>]+)",
        },
    }

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()

    def extract_from_file(self, file_path: Path) -> Dict[str, Set[str]]:
        """Extract signals from a single file."""
        signals = {
            "imports": set(),
            "decorators": set(),
            "inheritance": set(),
        }

        ext = file_path.suffix.lower()
        lang = self._get_lang_from_ext(ext)
        if not lang:
            return signals

        patterns = self.PATTERNS.get(lang, {})
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Read first 500 lines - usually enough for architectural signals
                lines = [f.readline() for _ in range(500)]
                content = "".join(lines)

                # Extract Imports
                if "import" in patterns:
                    for match in re.finditer(patterns["import"], content, re.MULTILINE):
                        signals["imports"].add(match.group(1))

                # Extract Decorators / Annotations
                dec_pattern = patterns.get("decorator") or patterns.get("annotation")
                if dec_pattern:
                    for match in re.finditer(dec_pattern, content):
                        signals["decorators"].add(match.group(1).split("(")[0])

                # Extract Inheritance
                if "inheritance" in patterns:
                    for match in re.finditer(patterns["inheritance"], content, re.MULTILINE):
                        bases = [b.strip() for b in match.group(1).split(",")]
                        signals["inheritance"].update(bases)
                elif "class_extends" in patterns:
                    for match in re.finditer(patterns["class_extends"], content, re.MULTILINE):
                        signals["inheritance"].add(match.group(1).strip())

        except Exception as e:
            logger.warning(f"Failed to extract signals from {file_path}: {e}")

        return signals

    def get_dna_snapshot(self, files: List[Path]) -> Dict[str, Any]:
        """Gathers deduplicated signals from a list of files."""
        all_signals = {
            "imports": set(),
            "decorators": set(),
            "inheritance": set(),
            "extensions": set(),
        }

        for f in files:
            file_signals = self.extract_from_file(self.root_path / f)
            all_signals["imports"].update(file_signals["imports"])
            all_signals["decorators"].update(file_signals["decorators"])
            all_signals["inheritance"].update(file_signals["inheritance"])
            all_signals["extensions"].add(f.suffix.lower())

        return {
            "top_imports": sorted(list(all_signals["imports"]))[:100], # Cap for LLM context
            "detected_decorators": sorted(list(all_signals["decorators"])),
            "detected_base_classes": sorted(list(all_signals["inheritance"])),
            "file_extensions": sorted(list(all_signals["extensions"])),
        }

    def _get_lang_from_ext(self, ext: str) -> str | None:
        if ext in [".py"]:
            return "python"
        if ext in [".js", ".ts", ".tsx", ".jsx"]:
            return "javascript"
        if ext in [".java", ".cs"]:
            return "java_csharp"
        return None
