from typing import Annotated, Any

from fastapi import APIRouter, Depends

from auth.dependencies import CurrentUser, require_permission
from services.approvals_store import count_pending_approvals
from services.prompt_service import prompt_service
from support.db import acquire

router = APIRouter(prefix="/api/governance", tags=["governance"])


@router.get("/overview")
async def governance_overview(
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    _ = user
    raw = prompt_service.load_raw()
    async with acquire() as connection:
        runs_7d = await connection.fetchval(
            """
            SELECT count(*) FROM agent_runs
            WHERE created_at >= now() - interval '7 days'
            """
        )
        grounded_rate = await connection.fetchval(
            """
            SELECT CASE
                     WHEN count(*) = 0 THEN NULL
                     ELSE round(
                       100.0 * count(*) FILTER (WHERE groundedness_passed) / count(*),
                       1
                     )
                   END
            FROM agent_runs
            WHERE created_at >= now() - interval '7 days'
              AND groundedness_passed IS NOT NULL
            """
        )
        pending_approvals = await count_pending_approvals()
        recent = await connection.fetch(
            """
            SELECT request_id, query, tools_used, latency_ms, groundedness_passed,
                   groundedness_explanation, created_at
            FROM agent_runs
            ORDER BY created_at DESC
            LIMIT 8
            """
        )
        tool_audit = await connection.fetchval(
            """
            SELECT count(*) FROM tool_call_audit
            WHERE created_at >= now() - interval '7 days'
            """
        )
    return {
        "prompt": {
            "name": raw["name"],
            "version": raw["version"],
            "labels": raw.get("labels") or [],
            "description": raw.get("description"),
        },
        "metrics": {
            "agent_runs_7d": runs_7d,
            "groundedness_pass_rate_7d": grounded_rate,
            "pending_approvals": pending_approvals,
            "tool_calls_7d": tool_audit,
        },
        "ai_system_register": [
            {
                "name": "Relay ReAct assistant",
                "owner": "Acme Operations Platform",
                "purpose": "Answer operational questions with tools, MCP, and RAG",
                "risk_level": "medium",
                "status": "active",
                "controls": [
                    "Keycloak RBAC",
                    "HITL for mutations",
                    "Groundedness verifier",
                    "Tool call audit",
                ],
            },
            {
                "name": "Knowledge ingest worker",
                "owner": "Acme Operations Platform",
                "purpose": "Chunk/embed knowledge with role ACLs",
                "risk_level": "low",
                "status": "active",
                "controls": ["allowed_roles filter before vector rank"],
            },
            {
                "name": "MCP sidecars (domain/filesystem/postgres)",
                "owner": "Acme Operations Platform",
                "purpose": "Extend agent tools via SSE MCP",
                "risk_level": "medium",
                "status": "active",
                "controls": ["Prefix RBAC", "SELECT-only Postgres MCP"],
            },
        ],
        "risk_register": [
            {
                "id": "RISK-01",
                "title": "Ungrounded factual claims",
                "level": "medium",
                "mitigation": "Post-answer groundedness check + audit explanation",
                "status": "mitigated",
            },
            {
                "id": "RISK-02",
                "title": "Unauthorized mutations",
                "level": "high",
                "mitigation": "RBAC + HITL approval queue for write tools",
                "status": "mitigated",
            },
            {
                "id": "RISK-03",
                "title": "Restricted knowledge leakage",
                "level": "high",
                "mitigation": "ACL filter on knowledge_chunks before ranking",
                "status": "mitigated",
            },
        ],
        "recent_runs": [dict(row) for row in recent],
    }


@router.get("/prompts")
async def prompt_versions(
    user: Annotated[CurrentUser, Depends(require_permission("approve_next_action"))],
) -> dict[str, Any]:
    _ = user
    raw = prompt_service.load_raw()
    return {
        "active": {
            "name": raw["name"],
            "version": raw["version"],
            "labels": raw.get("labels") or [],
            "description": raw.get("description"),
        }
    }
