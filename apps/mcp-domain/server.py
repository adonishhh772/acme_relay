"""Relay domain MCP server — Acme customer/case tools over SSE."""

from __future__ import annotations

import os

import asyncpg
from mcp.server.fastmcp import FastMCP

DATABASE_URL = os.environ["DATABASE_URL"]
PORT = int(os.environ.get("MCP_PORT", "8090"))

mcp = FastMCP("relay-domain")
_pool: asyncpg.Pool | None = None


async def pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=5)
    return _pool


@mcp.tool()
async def relay_get_customer_by_name(customer_name: str) -> dict:
    """Fetch customer profile by name or external id."""
    db = await pool()
    row = await db.fetchrow(
        """
        SELECT external_id, name, industry, tier, account_owner, region
        FROM customers
        WHERE name ILIKE $1 OR external_id ILIKE $1
        LIMIT 1
        """,
        f"%{customer_name}%",
    )
    return dict(row) if row else {"error": "not_found"}


@mcp.tool()
async def relay_list_open_issues(customer_name: str) -> dict:
    """List open issues for a customer."""
    db = await pool()
    rows = await db.fetch(
        """
        SELECT i.issue_key, i.title, i.status::text, i.priority::text, c.name AS customer_name
        FROM issues i
        JOIN customers c ON c.id = i.customer_id
        WHERE i.status IN ('open', 'in_progress')
          AND (c.name ILIKE $1 OR c.external_id ILIKE $1)
        ORDER BY i.priority
        """,
        f"%{customer_name}%",
    )
    return {"issues": [dict(row) for row in rows]}


if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = PORT
    mcp.run(transport="sse")
