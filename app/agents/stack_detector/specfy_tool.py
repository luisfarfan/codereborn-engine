import json
import subprocess
import uuid
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SpecfyToolInput(BaseModel):
    """Input for SpecfyTool."""
    repo_path: str = Field(
        ...,
        description="The absolute path to the repository directory to analyze."
    )


class SpecfyTool(BaseTool):
    name: str = "specfy_stack_analyser"
    description: str = (
        "Deterministic technology stack detector. Runs @specfy/stack-analyser CLI "
        "to identify frameworks, languages, and dependencies from file heuristics. "
        "Always returns a raw JSON structure."
    )
    args_schema: Type[BaseModel] = SpecfyToolInput

    def _run(self, repo_path: str) -> str:
        """
        Execute the specfy CLI and return the raw output.
        """
        if not Path(repo_path).exists():
            return f"Error: Repository path '{repo_path}' does not exist."

        # Use a relative path for the temporary JSON file (specfy CLI bug with absolute paths)
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)
        
        # Use a random-ish filename to avoid collisions
        temp_filename = f"specfy_{uuid.uuid4().hex[:8]}.json"
        temp_path = tmp_dir / temp_filename

        try:
            # Command: npx @specfy/stack-analyser <path> -o <temp_path>
            # We use str(temp_path) which is relative like 'tmp/specfy_abc.json'
            cmd = ["npx", "-y", "@specfy/stack-analyser", repo_path, "-o", str(temp_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return f"Error executing specfy-analyser (Code {result.returncode}): {result.stderr}"

            # Read the generated JSON file
            if not temp_path.exists():
                return (
                    f"Error: Specfy output file '{temp_path}' was not created. "
                    f"CLI stdout: {result.stdout}"
                )

            with open(temp_path, "r") as f:
                content = f.read()

            # Ensure it's valid JSON
            json.loads(content)
            return content

        except Exception as e:
            return f"Exception while running SpecfyTool: {str(e)}"
        finally:
            # Clean up the temporary file
            if temp_path.exists():
                temp_path.unlink()
