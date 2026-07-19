"""Postgres MCP — SELECT-only queries."""

from __future__ import annotations

import os
import re

import asyncpg
from mcp.server.fastmcp import FastMCP

DATABASE_URL = os.environ["DATABASE_URL"]
PORT = int(os.environ.get("MCP_PORT", "8092"))
FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke)\b", re.I)

mcp = FastMCP("relay-postgres")
_pool: asyncpg.Pool | None = None


async def pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=5)
    return _pool


@mcp.tool()
async def postgres_query(sql: str) -> dict:
    """Run a read-only SELECT against Relay Postgres."""
    stripped = sql.strip().rstrip(";")
    if not stripped.lower().startswith("select"):
        return {"error": "only_select_allowed"}
    if FORBIDDEN.search(stripped):
        return {"error": "forbidden_keyword"}
    db = await pool()
    rows = await db.fetch(stripped)
    return {"rows": [dict(row) for row in rows[:100]], "count": len(rows)}


if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = PORT
    mcp.run(transport="sse")
