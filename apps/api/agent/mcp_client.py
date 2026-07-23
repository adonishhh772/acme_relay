"""Load LangChain tools from Relay MCP servers (SSE) via langchain-mcp-adapters."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

from config import get_settings

logger = logging.getLogger("relay.mcp_client")

_client: Any | None = None
_cached_tools: list[BaseTool] | None = None
_load_error: str | None = None

MCP_SERVER_KEYS = ("domain", "filesystem", "postgres")

MCP_RESEARCH_TOOL_PREFIXES = (
    "domain_",
    "filesystem_",
    "postgres_",
)

MCP_SKILL_TOOL_PREFIXES = (
    "filesystem_",
    "domain_",
)

MCP_ACTION_TOOL_PREFIXES = ("filesystem_",)


def is_mcp_enabled() -> bool:
    settings = get_settings()
    if not settings.enable_mcp_agent_tools:
        return False
    return bool(settings.mcp_domain_url.strip())


def _sse_url(base: str) -> str:
    return f"{base.rstrip('/')}/sse"


def build_mcp_connections() -> dict[str, dict[str, Any]]:
    """Connection map for MultiServerMCPClient (testable without live servers)."""
    settings = get_settings()
    return {
        "domain": {
            "transport": "sse",
            "url": _sse_url(settings.mcp_domain_url),
            "timeout": settings.mcp_connect_timeout_seconds,
            "sse_read_timeout": settings.mcp_sse_read_timeout_seconds,
        },
        "filesystem": {
            "transport": "sse",
            "url": _sse_url(settings.mcp_filesystem_url),
            "timeout": settings.mcp_connect_timeout_seconds,
            "sse_read_timeout": settings.mcp_sse_read_timeout_seconds,
        },
        "postgres": {
            "transport": "sse",
            "url": _sse_url(settings.mcp_postgres_url),
            "timeout": settings.mcp_connect_timeout_seconds,
            "sse_read_timeout": settings.mcp_sse_read_timeout_seconds,
        },
    }


def _should_skip_mcp_tool(name: str) -> bool:
    lower = name.lower()
    return lower.endswith("_ping") or lower.split("_")[-1] == "ping"


def prefix_mcp_tool_name(server_name: str, tool_name: str) -> str:
    """Namespace MCP tools as ``{server}_{tool}`` for RBAC prefix matching.

    Newer ``langchain-mcp-adapters`` builds no longer accept
    ``tool_name_prefix=True`` on ``MultiServerMCPClient``, so we prefix
    explicitly after loading tools per server.
    """
    if tool_name.startswith(f"{server_name}_"):
        return tool_name
    return f"{server_name}_{tool_name}"


def _rename_mcp_tool(server_name: str, tool: BaseTool) -> StructuredTool:
    prefixed_name = prefix_mcp_tool_name(server_name, tool.name)

    async def _invoke(
        *args: Any,
        _base: BaseTool = tool,
        **kwargs: Any,
    ) -> Any:
        payload = kwargs if kwargs else (args[0] if args else {})
        return await _base.ainvoke(payload)

    return StructuredTool.from_function(
        coroutine=_invoke,
        name=prefixed_name,
        description=tool.description or f"MCP tool from {server_name}",
        args_schema=tool.args_schema,
    )


def is_mcp_research_tool(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in MCP_RESEARCH_TOOL_PREFIXES)


def is_mcp_skill_tool(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in MCP_SKILL_TOOL_PREFIXES)


def is_mcp_action_tool(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in MCP_ACTION_TOOL_PREFIXES)


async def warm_mcp_tools() -> None:
    """Pre-load MCP tools at startup (logs and caches; failures are non-fatal)."""
    await get_mcp_base_tools()


async def get_mcp_base_tools(*, force_reload: bool = False) -> list[BaseTool]:
    """Return cached MCP tools from all configured servers."""
    global _client, _cached_tools, _load_error

    if force_reload:
        _cached_tools = None
        _load_error = None

    if _cached_tools is not None:
        return _cached_tools

    if not is_mcp_enabled():
        _cached_tools = []
        return _cached_tools

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError as exc:
        _load_error = f"langchain-mcp-adapters not installed: {exc}"
        logger.warning(_load_error)
        _cached_tools = []
        return _cached_tools

    connections = build_mcp_connections()
    _client = MultiServerMCPClient(connections)

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            prefixed_tools: list[BaseTool] = []
            for server_name in MCP_SERVER_KEYS:
                server_tools = await _client.get_tools(server_name=server_name)
                for tool in server_tools:
                    if _should_skip_mcp_tool(tool.name):
                        continue
                    prefixed_tools.append(_rename_mcp_tool(server_name, tool))
            _cached_tools = prefixed_tools
            _load_error = None
            logger.info(
                "MCP tools loaded count=%s servers=%s",
                len(_cached_tools),
                ",".join(MCP_SERVER_KEYS),
            )
            return _cached_tools
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                await asyncio.sleep(2.0 * (attempt + 1))
    _load_error = str(last_exc) if last_exc else "unknown"
    logger.warning("MCP tool load failed: %s", _load_error)
    _cached_tools = []
    return _cached_tools


def mcp_load_status() -> dict[str, Any]:
    return {
        "enabled": is_mcp_enabled(),
        "loaded": _cached_tools is not None and len(_cached_tools or []) > 0,
        "tool_count": len(_cached_tools or []),
        "error": _load_error,
        "tool_names": [tool.name for tool in (_cached_tools or [])],
    }


def wrap_mcp_tools_for_context(
    base_tools: list[BaseTool],
    ctx: Any,
) -> list[StructuredTool]:
    """Wrap MCP tools so invocations flow through ToolContext audit and tracing."""
    wrapped: list[StructuredTool] = []

    for base in base_tools:

        async def _invoke(
            *args: Any,
            _base: BaseTool = base,
            _name: str = base.name,
            **kwargs: Any,
        ) -> str:
            payload = kwargs if kwargs else (args[0] if args else {})
            if not isinstance(payload, dict):
                payload = {"input": payload}
            return await ctx.run_mcp(_name, _base, payload)

        wrapped.append(
            StructuredTool.from_function(
                coroutine=_invoke,
                name=base.name,
                description=base.description or "MCP tool",
                args_schema=base.args_schema,
            )
        )

    return wrapped


def serialize_mcp_result(raw: Any) -> tuple[str, dict[str, Any]]:
    """Normalize LangChain MCP tool output to JSON string + dict for audit."""
    content: Any = raw
    if isinstance(raw, tuple) and raw:
        content = raw[0]

    if isinstance(content, str):
        text = content
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return text, parsed
        except json.JSONDecodeError:
            pass
        return text, {"content": text}

    if isinstance(content, list):
        text = json.dumps(content, default=str)
        return text, {"content": content}

    if isinstance(content, dict):
        text = json.dumps(content, default=str)
        return text, content

    text = str(content)
    return text, {"content": text}


def reset_mcp_cache_for_tests() -> None:
    """Clear module cache between unit tests."""
    global _client, _cached_tools, _load_error
    _client = None
    _cached_tools = None
    _load_error = None
