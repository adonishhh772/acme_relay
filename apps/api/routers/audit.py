from typing import Annotated, Any

from fastapi import APIRouter, Depends

from auth.dependencies import CurrentUser, require_permission
from support.db import acquire

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/tools")
async def tool_audit(
    user: Annotated[CurrentUser, Depends(require_permission("approve_next_action"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id::text, request_id, user_sub, tool_name, success, latency_ms, created_at
            FROM tool_call_audit
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
    return {"items": [dict(row) for row in rows]}


@router.get("/runs")
async def agent_runs(
    user: Annotated[CurrentUser, Depends(require_permission("approve_next_action"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id::text, request_id, user_sub, query, tools_used, latency_ms,
                   prompt_name, prompt_version, created_at
            FROM agent_runs
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
    return {"items": [dict(row) for row in rows]}
