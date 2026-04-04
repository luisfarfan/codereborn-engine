#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to sys.path to allow module imports
sys.path.append(str(Path(__file__).parent.parent))

from app.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
