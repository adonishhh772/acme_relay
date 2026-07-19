from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent import mcp_client
from agent.mcp_client import (
    get_mcp_base_tools,
    reset_mcp_cache_for_tests,
    serialize_mcp_result,
)
from agent.tools import ToolContext
from config import get_settings
from schemas.enums import Role


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    reset_mcp_cache_for_tests()
    get_settings.cache_clear()
    yield
    reset_mcp_cache_for_tests()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_mcp_base_tools_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "enable_mcp_agent_tools", False)
    tools = await get_mcp_base_tools()
    assert tools == []


@pytest.mark.asyncio
async def test_get_mcp_base_tools_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "enable_mcp_agent_tools", True)
    monkeypatch.setattr(settings, "mcp_domain_url", "http://mcp-domain:8090")

    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("langchain_mcp_adapters"):
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    tools = await get_mcp_base_tools(force_reload=True)
    assert tools == []
    assert "not installed" in (mcp_client.mcp_load_status().get("error") or "")


@pytest.mark.asyncio
async def test_get_mcp_base_tools_success(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "enable_mcp_agent_tools", True)
    monkeypatch.setattr(settings, "mcp_domain_url", "http://mcp-domain:8090")

    fake_tool = MagicMock()
    fake_tool.name = "domain_relay_list_open_issues"
    ping_tool = MagicMock()
    ping_tool.name = "domain_relay_ping"

    client = MagicMock()
    client.get_tools = AsyncMock(return_value=[fake_tool, ping_tool])

    with patch.dict(
        "sys.modules",
        {
            "langchain_mcp_adapters": MagicMock(),
            "langchain_mcp_adapters.client": MagicMock(),
        },
    ):
        import sys

        sys.modules["langchain_mcp_adapters.client"].MultiServerMCPClient = MagicMock(
            return_value=client
        )
        tools = await get_mcp_base_tools(force_reload=True)

    assert len(tools) == 1
    assert tools[0].name == "domain_relay_list_open_issues"


@pytest.mark.asyncio
async def test_run_mcp_permission_denied() -> None:
    ctx = ToolContext(
        user_sub="alice",
        username="alice",
        roles={Role.SALES},
        session_id="s1",
    )
    tool = MagicMock()
    tool.ainvoke = AsyncMock(return_value={"ok": True})
    text = await ctx.run_mcp("postgres_postgres_query", tool, {"sql": "select 1"})
    assert "permission_denied" in text
    assert ctx.tool_calls_log[-1]["source"] == "mcp"
    tool.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_run_mcp_success_audits(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = ToolContext(
        user_sub="bob",
        username="bob",
        roles={Role.SUPPORT},
        session_id="s1",
    )
    tool = MagicMock()
    tool.ainvoke = AsyncMock(return_value={"rows": [{"id": 1}]})

    connection = AsyncMock()
    acquire_cm = AsyncMock()
    acquire_cm.__aenter__.return_value = connection
    acquire_cm.__aexit__.return_value = None

    with (
        patch("agent.tools.acquire", return_value=acquire_cm),
        patch("agent.tools.log_tool_span"),
    ):
        text = await ctx.run_mcp("filesystem_fs_list_directory", tool, {"path": "."})

    assert "rows" in text
    assert ctx.tool_calls_log[-1]["source"] == "mcp"
    connection.execute.assert_awaited()


def test_serialize_mcp_result_list_and_fallback() -> None:
    text, parsed = serialize_mcp_result([{"a": 1}])
    assert parsed["content"][0]["a"] == 1
    assert "[" in text
    text2, parsed2 = serialize_mcp_result(42)
    assert parsed2["content"] == "42"
    assert text2 == "42"
