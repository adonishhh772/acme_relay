"""Unit tests for MCP client configuration (no live servers required)."""

from __future__ import annotations

import pytest

from agent.mcp_client import (
    MCP_SERVER_KEYS,
    _should_skip_mcp_tool,
    build_mcp_connections,
    is_mcp_enabled,
    is_mcp_research_tool,
    is_mcp_skill_tool,
    mcp_load_status,
    prefix_mcp_tool_name,
    reset_mcp_cache_for_tests,
    serialize_mcp_result,
    wrap_mcp_tools_for_context,
)
from config import get_settings


@pytest.fixture(autouse=True)
def _clear_mcp_cache() -> None:
    reset_mcp_cache_for_tests()
    get_settings.cache_clear()
    yield
    reset_mcp_cache_for_tests()
    get_settings.cache_clear()


def test_build_mcp_connections_has_three_servers() -> None:
    connections = build_mcp_connections()
    assert set(connections.keys()) == set(MCP_SERVER_KEYS)
    for config in connections.values():
        assert config["transport"] == "sse"
        assert config["url"].endswith("/sse")


def test_is_mcp_enabled_respects_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "enable_mcp_agent_tools", False)
    assert is_mcp_enabled() is False
    monkeypatch.setattr(settings, "enable_mcp_agent_tools", True)
    monkeypatch.setattr(settings, "mcp_domain_url", "http://mcp-domain:8090")
    assert is_mcp_enabled() is True


def test_should_skip_ping_tools() -> None:
    assert _should_skip_mcp_tool("domain_relay_ping") is True
    assert _should_skip_mcp_tool("relay_ping") is True
    assert _should_skip_mcp_tool("filesystem_fs_read_file") is False


def test_prefix_mcp_tool_name() -> None:
    assert prefix_mcp_tool_name("domain", "relay_list_open_issues") == (
        "domain_relay_list_open_issues"
    )
    assert prefix_mcp_tool_name("domain", "domain_relay_list_open_issues") == (
        "domain_relay_list_open_issues"
    )
    # Tool already namespaced with server id — do not double-prefix.
    assert prefix_mcp_tool_name("postgres", "postgres_query") == "postgres_query"


def test_mcp_tool_prefix_classifiers() -> None:
    assert is_mcp_research_tool("postgres_postgres_query") is True
    assert is_mcp_research_tool("get_open_issues") is False
    assert is_mcp_skill_tool("filesystem_fs_list_directory") is True


def test_serialize_mcp_result_dict() -> None:
    text, parsed = serialize_mcp_result({"ok": True, "rows": []})
    assert "ok" in text
    assert parsed["ok"] is True


def test_serialize_mcp_result_json_string() -> None:
    text, parsed = serialize_mcp_result('{"ok": true}')
    assert parsed["ok"] is True
    assert "ok" in text


def test_mcp_load_status_default() -> None:
    status = mcp_load_status()
    assert "enabled" in status
    assert status["tool_count"] == 0


@pytest.mark.asyncio
async def test_wrap_mcp_tools_for_context_invokes_run_mcp() -> None:
    class FakeTool:
        name = "domain_relay_list_open_issues"
        description = "list issues"
        args_schema = None

        async def ainvoke(self, payload: dict) -> dict:
            return {"ok": True, "payload": payload}

    class FakeCtx:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        async def run_mcp(self, name: str, tool: object, args: dict) -> str:
            self.calls.append((name, args))
            return '{"ok": true}'

    ctx = FakeCtx()
    wrapped = wrap_mcp_tools_for_context([FakeTool()], ctx)
    assert len(wrapped) == 1
    result = await wrapped[0].ainvoke({"customer_name": "VaultLedger"})
    assert result == '{"ok": true}'
    assert ctx.calls[0][0] == "domain_relay_list_open_issues"
