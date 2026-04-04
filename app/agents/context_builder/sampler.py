import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Max lines for sample content to avoid overloading context
MAX_SAMPLE_LINES = 200

class ArchitecturalSampler:
    """
    Extracts high-value code samples for LLM context.
    Focuses on signatures, imports, and core logic.
    Deterministic — zero LLM tokens.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path

    def sample(self, file_path: Path, role: str, zone: str) -> Dict[str, Any]:
        """
        Extracts a meaningful excerpt from a file.
        """
        full_path = self.root_path / file_path
        
        try:
            if not full_path.exists():
                return {
                    "file_path": str(file_path),
                    "zone": zone,
                    "role": role,
                    "content_excerpt": "[File not found]",
                    "selection_reason": "rank_missing_file"
                }
            
            # Read first N lines
            with open(full_path, "r", errors="ignore", encoding="utf-8") as f:
                lines = f.readlines()
                
            sample_lines = lines[:MAX_SAMPLE_LINES]
            content = "".join(sample_lines)
            
            if len(lines) > MAX_SAMPLE_LINES:
                content += f"\n\n... [Truncated {len(lines) - MAX_SAMPLE_LINES} lines] ..."

            return {
                "file_path": str(file_path),
                "zone": zone,
                "role": role,
                "content_excerpt": content,
                "selection_reason": f"High architectural ranking - Role: {role}"
            }
            
        except Exception as e:
            logger.error(f"Failed to sample file {file_path}: {str(e)}")
            return {
                "file_path": str(file_path),
                "zone": zone,
                "role": role,
                "content_excerpt": f"[Error sampling: {str(e)}]",
                "selection_reason": "error_during_sampling"
            }
