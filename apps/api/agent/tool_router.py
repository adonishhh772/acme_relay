import json
import time
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.mcp_client import (
    get_mcp_base_tools,
    is_mcp_enabled,
    wrap_mcp_tools_for_context,
)
from agent.tools import (
    ToolContext,
    create_next_action,
    get_customer_profile_by_name,
    get_open_issues,
    search_knowledge,
    summarize_issue_history,
    update_issue,
)
from skills.registry import invoke_skill
from support.db import acquire
from telemetry.langfuse_tracing import log_tool_span


class CustomerNameArgs(BaseModel):
    customer_name: str = Field(..., description="Customer display name or external id")


class IssueKeyArgs(BaseModel):
    issue_key: str = Field(..., description="Case key such as CASE-2001")


class CreateActionArgs(BaseModel):
    issue_key: str
    action_text: str
    owner: str | None = None


class UpdateIssueArgs(BaseModel):
    issue_key: str
    status: str | None = None
    comment: str | None = None


class SearchArgs(BaseModel):
    query: str = Field(..., description="Natural language knowledge query")


async def _audit(
    ctx: ToolContext,
    tool_name: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    latency_ms: int,
) -> None:
    role_values = [role.value for role in ctx.roles]
    async with acquire() as connection:
        await connection.execute(
            """
            INSERT INTO tool_call_audit (
                request_id, user_sub, user_roles, tool_name, arguments,
                result_summary, latency_ms, success, source
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)
            """,
            ctx.request_id,
            ctx.user_sub,
            role_values,
            tool_name,
            json.dumps(arguments),
            json.dumps(result)[:2000],
            latency_ms,
            bool(result.get("ok", False)),
            "native",
        )
    log_tool_span(
        request_id=ctx.request_id,
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        latency_ms=latency_ms,
        user_sub=ctx.user_sub,
        roles=role_values,
    )
    ctx.tool_calls_log.append(
        {
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
            "latency_ms": latency_ms,
            "source": "native",
        }
    )


async def build_langchain_tools(ctx: ToolContext) -> list[StructuredTool]:
    async def wrap(tool_name: str, coroutine, payload: dict[str, Any]) -> str:
        started = time.perf_counter()
        result = await coroutine
        latency_ms = int((time.perf_counter() - started) * 1000)
        await _audit(ctx, tool_name, payload, result, latency_ms)
        return json.dumps(result, default=str)

    async def customer_profile(customer_name: str) -> str:
        return await wrap(
            "get_customer_profile_by_name",
            get_customer_profile_by_name(ctx, customer_name),
            {"customer_name": customer_name},
        )

    async def open_issues(customer_name: str) -> str:
        return await wrap(
            "get_open_issues",
            get_open_issues(ctx, customer_name),
            {"customer_name": customer_name},
        )

    async def summarize(issue_key: str) -> str:
        return await wrap(
            "summarize_issue_history",
            summarize_issue_history(ctx, issue_key),
            {"issue_key": issue_key},
        )

    async def create_action(
        issue_key: str, action_text: str, owner: str | None = None
    ) -> str:
        return await wrap(
            "create_next_action",
            create_next_action(ctx, issue_key, action_text, owner),
            {"issue_key": issue_key, "action_text": action_text, "owner": owner},
        )

    async def update(
        issue_key: str, status: str | None = None, comment: str | None = None
    ) -> str:
        return await wrap(
            "update_issue",
            update_issue(ctx, issue_key, status, comment),
            {"issue_key": issue_key, "status": status, "comment": comment},
        )

    async def knowledge(query: str) -> str:
        return await wrap(
            "search_knowledge",
            search_knowledge(ctx, query),
            {"query": query},
        )

    def skill_tool(skill_name: str) -> StructuredTool:
        async def runner(customer_name: str) -> str:
            return await wrap(
                skill_name,
                invoke_skill(ctx, skill_name, customer_name),
                {"customer_name": customer_name},
            )

        return StructuredTool.from_function(
            coroutine=runner,
            name=skill_name,
            description=f"Reusable Relay skill: {skill_name}",
            args_schema=CustomerNameArgs,
        )

    tools: list[StructuredTool] = [
        StructuredTool.from_function(
            coroutine=customer_profile,
            name="get_customer_profile_by_name",
            description="Retrieve customer profile by name or external id",
            args_schema=CustomerNameArgs,
        ),
        StructuredTool.from_function(
            coroutine=open_issues,
            name="get_open_issues",
            description="List open/in-progress issues for a customer",
            args_schema=CustomerNameArgs,
        ),
        StructuredTool.from_function(
            coroutine=summarize,
            name="summarize_issue_history",
            description="Summarise history/updates for a specific issue key",
            args_schema=IssueKeyArgs,
        ),
        StructuredTool.from_function(
            coroutine=create_action,
            name="create_next_action",
            description="Propose a next action for an issue (requires approval)",
            args_schema=CreateActionArgs,
        ),
        StructuredTool.from_function(
            coroutine=update,
            name="update_issue",
            description="Propose an issue status/comment update (requires approval)",
            args_schema=UpdateIssueArgs,
        ),
        StructuredTool.from_function(
            coroutine=knowledge,
            name="search_knowledge",
            description="RBAC-aware semantic search over knowledge base (pgvector)",
            args_schema=SearchArgs,
        ),
        skill_tool("run_escalation_summary_skill"),
        skill_tool("run_sla_breach_assessment_skill"),
        skill_tool("run_issue_triage_skill"),
        skill_tool("run_shift_handoff_skill"),
    ]

    if is_mcp_enabled():
        mcp_base = await get_mcp_base_tools()
        if not mcp_base:
            mcp_base = await get_mcp_base_tools(force_reload=True)
        if mcp_base:
            tools.extend(wrap_mcp_tools_for_context(mcp_base, ctx))

    return tools
