"""
ctfd-mcp: MCP server for CTFd user-scope operations.

Public entrypoints:
- `ctfd_mcp.main.main` function (console script `ctfd-mcp`)
- `ctfd_mcp.server.mcp` FastMCP instance
"""

from .main import main
from .server import mcp

__all__ = ["main", "mcp"]
