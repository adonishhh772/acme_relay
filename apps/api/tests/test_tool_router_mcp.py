from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent import tool_router
from agent.tools import ToolContext
from schemas.enums import Role


class _Args(BaseModel):
    customer_name: str = Field(...)


@pytest.mark.asyncio
async def test_build_langchain_tools_merges_mcp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = StructuredTool.from_function(
        coroutine=AsyncMock(return_value='{"ok": true}'),
        name="domain_relay_list_open_issues",
        description="mcp domain tool",
        args_schema=_Args,
    )

    monkeypatch.setattr(tool_router, "is_mcp_enabled", lambda: True)
    monkeypatch.setattr(
        tool_router,
        "get_mcp_base_tools",
        AsyncMock(return_value=[base]),
    )
    monkeypatch.setattr(
        tool_router,
        "wrap_mcp_tools_for_context",
        lambda tools, ctx: tools,
    )

    ctx = ToolContext(
        user_sub="bob",
        username="bob",
        roles={Role.SUPPORT},
        session_id="s1",
    )
    tools = await tool_router.build_langchain_tools(ctx)
    names = {tool.name for tool in tools}
    assert "get_open_issues" in names
    assert "domain_relay_list_open_issues" in names
    assert "search_knowledge" in names


@pytest.mark.asyncio
async def test_build_langchain_tools_skips_mcp_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tool_router, "is_mcp_enabled", lambda: False)
    get_tools = AsyncMock()
    monkeypatch.setattr(tool_router, "get_mcp_base_tools", get_tools)

    ctx = ToolContext(
        user_sub="bob",
        username="bob",
        roles={Role.SUPPORT},
        session_id="s1",
    )
    tools = await tool_router.build_langchain_tools(ctx)
    names = {tool.name for tool in tools}
    assert "get_open_issues" in names
    assert not any(name.startswith("domain_") for name in names)
    get_tools.assert_not_called()
