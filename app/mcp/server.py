import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("CodeReborn Engine")

# Base path for AI specs
AI_SPEC_DIR = Path(__file__).parent.parent.parent / "docs" / "ai_spec"

def _load_spec(filename: str) -> dict[str, Any]:
    """Helper to load a JSON spec file."""
    path = AI_SPEC_DIR / filename
    if not path.exists():
        return {"error": f"Spec file {filename} not found at {path}"}
    
    with open(path, "r") as f:
        return json.load(f)

@mcp.tool()
def get_system_overview() -> dict[str, Any]:
    """
    Returns a high-level overview of the CodeReborn Engine system, 
    including vision, core stack, key components, and crucial rules.
    Used to understand the system's purpose and architecture.
    """
    return _load_spec("index.json")

@mcp.tool()
def get_api_contracts() -> dict[str, Any]:
    """
    Returns full REST API contracts for the Repo Intelligence Interface.
    Includes all endpoints organized by domain (Understanding, Navigation, Context, etc.)
    with request/response schemas.
    """
    return _load_spec("06_api_contracts.json")

@mcp.tool()
def get_data_contracts() -> dict[str, Any]:
    """
    Returns formal schemas for every agent output and internal data structures.
    Pydantic-ready models for Stack Reports, System Maps, Tech Debt findings, etc.
    """
    return _load_spec("05_data_contracts.json")

@mcp.tool()
def get_agent_specs() -> dict[str, Any]:
    """
    Returns the specifications for all AI agents in the pipeline (StackDetector, 
    SystemMapper, TechDebtAnalyzer, etc.), including their roles, rules, and facts.
    """
    return _load_spec("03_pipeline_agents.json")

@mcp.tool()
def get_implementation_map() -> dict[str, Any]:
    """
    Returns a mapping between the system specifications and the actual code implementation.
    Includes Python file paths, class names, and models for every component.
    """
    return _load_spec("07_implementation_map.json")

@mcp.tool()
def get_api_domains() -> dict[str, Any]:
    """
    Returns the domains and rules for the Repo Intelligence API integration.
    Includes rate limits, auth requirements, and extension points.
    """
    return _load_spec("04_repo_intelligence_api.json")

if __name__ == "__main__":
    mcp.run()
