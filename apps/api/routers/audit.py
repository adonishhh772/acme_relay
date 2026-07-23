"""Enterprise audit API — durable trail of agent runs, tool calls, and HITL decisions."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query

from auth.dependencies import CurrentUser, require_permission
from services.observability_links import (
    attach_observability_links,
    observability_catalog,
)
from support.db import acquire

router = APIRouter(prefix="/api/audit", tags=["audit"])

AuditTab = Literal["tools", "runs", "approvals"]


def _serialize_row(row: Any) -> dict[str, Any]:
    payload = dict(row)
    created = payload.get("created_at")
    if created is not None and hasattr(created, "isoformat"):
        payload["created_at"] = created.isoformat()
    decided = payload.get("decided_at")
    if decided is not None and hasattr(decided, "isoformat"):
        payload["decided_at"] = decided.isoformat()
    arguments = payload.get("arguments")
    if isinstance(arguments, str):
        try:
            payload["arguments"] = json.loads(arguments)
        except json.JSONDecodeError:
            pass
    return payload


@router.get("/summary")
async def audit_summary(
    user: Annotated[CurrentUser, Depends(require_permission("view_audit"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        tool_stats = await connection.fetchrow(
            """
            SELECT
                count(*)::int AS total_tool_calls,
                count(*) FILTER (WHERE success)::int AS tool_successes,
                count(*) FILTER (WHERE NOT success)::int AS tool_failures,
                count(*) FILTER (WHERE source = 'mcp')::int AS mcp_calls,
                count(*) FILTER (WHERE source = 'native')::int AS native_calls,
                round(avg(latency_ms)::numeric, 1) AS avg_tool_latency_ms
            FROM tool_call_audit
            WHERE created_at > now() - interval '7 days'
            """
        )
        run_stats = await connection.fetchrow(
            """
            SELECT
                count(*)::int AS total_runs,
                count(*) FILTER (WHERE groundedness_passed IS TRUE)::int AS grounded_pass,
                count(*) FILTER (WHERE groundedness_passed IS FALSE)::int AS grounded_fail,
                round(avg(latency_ms)::numeric, 1) AS avg_run_latency_ms
            FROM agent_runs
            WHERE created_at > now() - interval '7 days'
            """
        )
        approval_stats = await connection.fetchrow(
            """
            SELECT
                count(*) FILTER (WHERE status = 'pending')::int AS pending,
                count(*) FILTER (WHERE status = 'approved')::int AS approved,
                count(*) FILTER (WHERE status = 'rejected')::int AS rejected
            FROM pending_approvals
            WHERE created_at > now() - interval '7 days'
            """
        )
        top_tools = await connection.fetch(
            """
            SELECT tool_name, count(*)::int AS calls
            FROM tool_call_audit
            WHERE created_at > now() - interval '7 days'
            GROUP BY tool_name
            ORDER BY calls DESC
            LIMIT 8
            """
        )

    grounded_total = (run_stats["grounded_pass"] or 0) + (run_stats["grounded_fail"] or 0)
    grounded_rate = (
        round(100.0 * (run_stats["grounded_pass"] or 0) / grounded_total, 1)
        if grounded_total
        else None
    )

    return {
        "window": "7d",
        "what_we_audit": [
            {
                "stream": "tool_calls",
                "table": "tool_call_audit",
                "description": (
                    "Every native and MCP tool invocation: who called it, arguments, "
                    "success/failure, latency, and source (native vs mcp)."
                ),
            },
            {
                "stream": "agent_runs",
                "table": "agent_runs",
                "description": (
                    "Each assistant chat run: user query, tools used, latency, prompt "
                    "version, and groundedness pass/fail with explanation."
                ),
            },
            {
                "stream": "hitl_approvals",
                "table": "pending_approvals",
                "description": (
                    "Human-in-the-loop decisions for mutating actions "
                    "(create next action / update issue): requester, decision, approver."
                ),
            },
        ],
        "tool_calls_7d": tool_stats["total_tool_calls"] or 0,
        "tool_failures_7d": tool_stats["tool_failures"] or 0,
        "mcp_calls_7d": tool_stats["mcp_calls"] or 0,
        "native_calls_7d": tool_stats["native_calls"] or 0,
        "avg_tool_latency_ms": (
            float(tool_stats["avg_tool_latency_ms"])
            if tool_stats["avg_tool_latency_ms"] is not None
            else None
        ),
        "agent_runs_7d": run_stats["total_runs"] or 0,
        "groundedness_pass_rate_7d": grounded_rate,
        "avg_run_latency_ms": (
            float(run_stats["avg_run_latency_ms"])
            if run_stats["avg_run_latency_ms"] is not None
            else None
        ),
        "approvals_pending_7d": approval_stats["pending"] or 0,
        "approvals_approved_7d": approval_stats["approved"] or 0,
        "approvals_rejected_7d": approval_stats["rejected"] or 0,
        "top_tools_7d": [dict(row) for row in top_tools],
        "observability": observability_catalog(),
    }


@router.get("/observability")
async def audit_observability(
    user: Annotated[CurrentUser, Depends(require_permission("view_audit"))],
) -> dict[str, Any]:
    _ = user
    return observability_catalog()


@router.get("/tools")
async def tool_audit(
    user: Annotated[CurrentUser, Depends(require_permission("view_audit"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    source: str | None = Query(default=None),
    success: bool | None = Query(default=None),
    tool_name: str | None = Query(default=None),
) -> dict[str, Any]:
    _ = user
    filters = ["TRUE"]
    params: list[Any] = []

    if source in {"native", "mcp"}:
        params.append(source)
        filters.append(f"source = ${len(params)}")
    if success is not None:
        params.append(success)
        filters.append(f"success = ${len(params)}")
    if tool_name:
        params.append(f"%{tool_name.strip()}%")
        filters.append(f"tool_name ILIKE ${len(params)}")

    where_sql = " AND ".join(filters)
    offset = (page - 1) * page_size
    params.extend([page_size, offset])

    async with acquire() as connection:
        total = await connection.fetchval(
            f"SELECT count(*) FROM tool_call_audit WHERE {where_sql}",
            *params[:-2],
        )
        rows = await connection.fetch(
            f"""
            SELECT id::text, request_id, user_sub, user_roles, tool_name, arguments,
                   result_summary, latency_ms, success, source, created_at
            FROM tool_call_audit
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

    return {
        "items": [attach_observability_links(_serialize_row(row)) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": int(total or 0),
        "observability": observability_catalog(),
    }


@router.get("/runs")
async def agent_runs_audit(
    user: Annotated[CurrentUser, Depends(require_permission("view_audit"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    groundedness: str | None = Query(default=None),
) -> dict[str, Any]:
    _ = user
    filters = ["TRUE"]
    params: list[Any] = []

    if groundedness == "pass":
        filters.append("groundedness_passed IS TRUE")
    elif groundedness == "fail":
        filters.append("groundedness_passed IS FALSE")
    elif groundedness == "unset":
        filters.append("groundedness_passed IS NULL")

    where_sql = " AND ".join(filters)
    offset = (page - 1) * page_size
    params.extend([page_size, offset])

    async with acquire() as connection:
        total = await connection.fetchval(
            f"SELECT count(*) FROM agent_runs WHERE {where_sql}",
            *params[:-2],
        )
        rows = await connection.fetch(
            f"""
            SELECT id::text, request_id, user_sub, query, answer, tools_used, latency_ms,
                   prompt_name, prompt_version, groundedness_passed,
                   groundedness_explanation, created_at
            FROM agent_runs
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

    return {
        "items": [attach_observability_links(_serialize_row(row)) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": int(total or 0),
        "observability": observability_catalog(),
    }


@router.get("/approvals")
async def approvals_audit(
    user: Annotated[CurrentUser, Depends(require_permission("view_audit"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    _ = user
    filters = ["TRUE"]
    params: list[Any] = []

    if status in {"pending", "approved", "rejected", "completed"}:
        params.append(status)
        filters.append(f"status::text = ${len(params)}")

    where_sql = " AND ".join(filters)
    offset = (page - 1) * page_size
    params.extend([page_size, offset])

    async with acquire() as connection:
        total = await connection.fetchval(
            f"SELECT count(*) FROM pending_approvals WHERE {where_sql}",
            *params[:-2],
        )
        rows = await connection.fetch(
            f"""
            SELECT id::text, request_id, session_id, tool_name, arguments,
                   created_by_sub, status::text AS status, decided_by_sub,
                   decided_at, created_at
            FROM pending_approvals
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )

    return {
        "items": [attach_observability_links(_serialize_row(row)) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": int(total or 0),
        "observability": observability_catalog(),
    }
