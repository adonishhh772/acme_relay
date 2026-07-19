"""Filesystem MCP — read-only knowledge files."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(os.environ.get("KNOWLEDGE_ROOT", "/data/knowledge")).resolve()
PORT = int(os.environ.get("MCP_PORT", "8091"))
mcp = FastMCP("relay-filesystem")


def _safe(path: str) -> Path:
    candidate = (ROOT / path).resolve()
    if not str(candidate).startswith(str(ROOT)):
        raise ValueError("Path escapes knowledge root")
    return candidate


@mcp.tool()
def fs_list_directory(relative_path: str = ".") -> dict:
    """List files under the knowledge root."""
    target = _safe(relative_path)
    if not target.exists():
        return {"error": "not_found"}
    entries = []
    for item in sorted(target.iterdir()):
        entries.append({"name": item.name, "is_dir": item.is_dir()})
    return {"path": relative_path, "entries": entries}


@mcp.tool()
def fs_read_file(relative_path: str) -> dict:
    """Read a UTF-8 text file from the knowledge root."""
    target = _safe(relative_path)
    if not target.is_file():
        return {"error": "not_found"}
    return {"path": relative_path, "content": target.read_text(encoding="utf-8")}


if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = PORT
    mcp.run(transport="sse")
