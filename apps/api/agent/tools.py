from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from auth.rbac import requires_hitl, tool_allowed
from knowledge.search import search_knowledge_rbac
from schemas.enums import Role
from support.db import acquire
from telemetry.langfuse_tracing import log_tool_span


@dataclass
class ToolContext:
    user_sub: str
    username: str
    roles: set[Role]
    session_id: str
    request_id: str = field(default_factory=lambda: uuid4().hex)
    pending_approvals: list[dict[str, Any]] = field(default_factory=list)
    tool_calls_log: list[dict[str, Any]] = field(default_factory=list)
    progress: Any | None = None

    async def emit_progress(self, event_type: str, **payload: Any) -> None:
        if self.progress is None:
            return
        await self.progress.emit(event_type, **payload)

    async def run_mcp(self, name: str, tool: Any, args: dict[str, Any]) -> str:
        """Invoke an MCP tool with RBAC, audit, and groundedness logging."""
        from agent.mcp_client import serialize_mcp_result

        if not tool_allowed(self.roles, name):
            denied = _denied(name)
            self.tool_calls_log.append(
                {
                    "tool": name,
                    "arguments": args,
                    "result": denied,
                    "latency_ms": 0,
                    "source": "mcp",
                }
            )
            return json.dumps(denied, default=str)

        await self.emit_progress("tool_start", tool=name, source="mcp")
        started = time.perf_counter()
        try:
            raw = await tool.ainvoke(args)
            text, result = serialize_mcp_result(raw)
            if "ok" not in result:
                result = {"ok": True, **result}
        except Exception as exc:
            result = {"ok": False, "error": "mcp_call_failed", "message": str(exc)}
            text = json.dumps(result)
        latency_ms = int((time.perf_counter() - started) * 1000)
        await self.emit_progress(
            "tool_done",
            tool=name,
            source="mcp",
            latency_ms=latency_ms,
            status="ok" if result.get("ok", False) else "error",
        )
        role_values = [role.value for role in self.roles]
        async with acquire() as connection:
            await connection.execute(
                """
                INSERT INTO tool_call_audit (
                    request_id, user_sub, user_roles, tool_name, arguments,
                    result_summary, latency_ms, success, source
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)
                """,
                self.request_id,
                self.user_sub,
                role_values,
                name,
                json.dumps(args),
                json.dumps(result)[:2000],
                latency_ms,
                bool(result.get("ok", False)) and "error" not in result,
                "mcp",
            )
        log_tool_span(
            request_id=self.request_id,
            tool_name=name,
            arguments=args,
            result=result,
            latency_ms=latency_ms,
            user_sub=self.user_sub,
            roles=role_values,
        )
        self.tool_calls_log.append(
            {
                "tool": name,
                "arguments": args,
                "result": result,
                "latency_ms": latency_ms,
                "source": "mcp",
            }
        )
        return text


def _denied(tool_name: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "permission_denied",
        "tool": tool_name,
        "message": f"Your role cannot use {tool_name}.",
    }


async def get_customer_profile_by_name(
    ctx: ToolContext, customer_name: str
) -> dict[str, Any]:
    if not tool_allowed(ctx.roles, "get_customer_profile_by_name"):
        return _denied("get_customer_profile_by_name")
    async with acquire() as connection:
        row = await connection.fetchrow(
            """
            SELECT external_id, name, industry, tier, account_owner, support_manager,
                   account_manager, region, contract_value_gbp, renewal_date
            FROM customers
            WHERE is_active = true
              AND (name ILIKE $1 OR external_id ILIKE $1)
            ORDER BY name
            LIMIT 1
            """,
            f"%{customer_name.strip()}%",
        )
    if row is None:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"No customer matching '{customer_name}'.",
        }
    customer = dict(row)
    if customer.get("renewal_date") is not None:
        customer["renewal_date"] = customer["renewal_date"].isoformat()
    if customer.get("contract_value_gbp") is not None:
        customer["contract_value_gbp"] = float(customer["contract_value_gbp"])
    return {"ok": True, "customer": customer}


async def get_open_issues(ctx: ToolContext, customer_name: str) -> dict[str, Any]:
    if not tool_allowed(ctx.roles, "get_open_issues"):
        return _denied("get_open_issues")
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT i.issue_key, i.title, i.status::text, i.priority::text,
                   i.assigned_to, i.sla_due_at, c.name AS customer_name, c.external_id
            FROM issues i
            JOIN customers c ON c.id = i.customer_id
            WHERE i.status IN ('open', 'in_progress')
              AND (c.name ILIKE $1 OR c.external_id ILIKE $1)
            ORDER BY
              CASE i.priority
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4
              END,
              i.created_at
            """,
            f"%{customer_name.strip()}%",
        )
    return {
        "ok": True,
        "customer_query": customer_name,
        "open_issues": [dict(row) for row in rows],
        "count": len(rows),
    }


async def summarize_issue_history(ctx: ToolContext, issue_key: str) -> dict[str, Any]:
    if not tool_allowed(ctx.roles, "summarize_issue_history"):
        return _denied("summarize_issue_history")
    async with acquire() as connection:
        issue = await connection.fetchrow(
            """
            SELECT i.issue_key, i.title, i.status::text, i.priority::text, i.description,
                   c.name AS customer_name
            FROM issues i
            JOIN customers c ON c.id = i.customer_id
            WHERE i.issue_key = $1
            """,
            issue_key.strip().upper(),
        )
        if issue is None:
            return {
                "ok": False,
                "error": "not_found",
                "message": f"Issue {issue_key} not found.",
            }
        updates = await connection.fetch(
            """
            SELECT author, body, is_internal, created_at
            FROM issue_updates
            WHERE issue_id = (SELECT id FROM issues WHERE issue_key = $1)
            ORDER BY created_at
            """,
            issue_key.strip().upper(),
        )
    visible_updates = []
    for update in updates:
        if (
            update["is_internal"]
            and Role.SALES in ctx.roles
            and Role.SUPPORT not in ctx.roles
            and Role.ADMIN not in ctx.roles
        ):
            continue
        visible_updates.append(
            {
                "author": update["author"],
                "body": update["body"],
                "created_at": update["created_at"].isoformat(),
                "is_internal": update["is_internal"],
            }
        )
    return {
        "ok": True,
        "issue": dict(issue),
        "updates": visible_updates,
        "summary_points": [item["body"] for item in visible_updates[-5:]],
    }


async def create_next_action(
    ctx: ToolContext,
    issue_key: str,
    action_text: str,
    owner: str | None = None,
) -> dict[str, Any]:
    if not tool_allowed(ctx.roles, "create_next_action"):
        return _denied("create_next_action")
    if requires_hitl("create_next_action"):
        pending = {
            "approval_id": uuid4().hex,
            "tool": "create_next_action",
            "issue_key": issue_key.strip().upper(),
            "action_text": action_text,
            "owner": owner or ctx.username,
            "requested_by": ctx.username,
            "status": "pending_approval",
        }
        ctx.pending_approvals.append(pending)
        return {
            "ok": True,
            "pending_approval": True,
            "message": "Next action staged for human approval.",
            "approval": pending,
        }
    return {"ok": False, "error": "unexpected"}


async def update_issue(
    ctx: ToolContext,
    issue_key: str,
    status: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    if not tool_allowed(ctx.roles, "update_issue"):
        return _denied("update_issue")
    pending = {
        "approval_id": uuid4().hex,
        "tool": "update_issue",
        "issue_key": issue_key.strip().upper(),
        "status": status,
        "comment": comment,
        "requested_by": ctx.username,
        "status_label": "pending_approval",
    }
    ctx.pending_approvals.append(pending)
    return {
        "ok": True,
        "pending_approval": True,
        "message": "Issue update staged for human approval.",
        "approval": pending,
    }


async def search_knowledge(ctx: ToolContext, query: str) -> dict[str, Any]:
    if not tool_allowed(ctx.roles, "search_knowledge"):
        return _denied("search_knowledge")
    chunks = await search_knowledge_rbac(query, ctx.roles)
    return {
        "ok": True,
        "query": query,
        "results": chunks,
        "count": len(chunks),
        "note": "Results are filtered by your Keycloak roles before ranking.",
    }
