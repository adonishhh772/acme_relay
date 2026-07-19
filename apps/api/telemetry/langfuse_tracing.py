"""Langfuse integration: LangChain callbacks + explicit tool/run spans."""

from __future__ import annotations

import logging
from typing import Any

from config import Settings, get_settings

logger = logging.getLogger("relay.langfuse")

_client = None


def get_langfuse_client(settings: Settings | None = None):
    global _client
    settings = settings or get_settings()
    if not (
        settings.enable_langfuse
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    ):
        return None
    if _client is not None:
        return _client
    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        return _client
    except Exception:
        logger.exception("Failed to create Langfuse client")
        return None


def build_langfuse_callbacks(
    settings: Settings,
    *,
    session_id: str,
    user_id: str,
    request_id: str,
    prompt_name: str,
    prompt_version: int,
    roles: str,
) -> list[Any]:
    if not (
        settings.enable_langfuse
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    ):
        return []
    try:
        from langfuse.callback import CallbackHandler

        handler_kwargs: dict[str, Any] = {
            "public_key": settings.langfuse_public_key,
            "secret_key": settings.langfuse_secret_key,
            "host": settings.langfuse_host,
            "session_id": session_id,
            "user_id": user_id,
            "metadata": {
                "request_id": request_id,
                "prompt_name": prompt_name,
                "prompt_version": prompt_version,
                "user_roles": roles,
                "product": "relay",
            },
            "tags": ["relay", "agent", *roles.split(",")[:3]],
        }
        try:
            handler = CallbackHandler(**handler_kwargs, trace_name="relay-agent-run")
        except TypeError:
            handler = CallbackHandler(**handler_kwargs)
        return [handler]
    except Exception:
        logger.exception("Failed to create Langfuse CallbackHandler")
        return []


def log_tool_span(
    *,
    request_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    latency_ms: int,
    user_sub: str,
    roles: list[str],
) -> None:
    """Mirror Postgres tool_call_audit into Langfuse as an explicit span/event."""
    client = get_langfuse_client()
    if client is None:
        return
    try:
        trace = client.trace(
            id=request_id,
            name="relay-agent-run",
            user_id=user_sub,
            metadata={"user_roles": roles, "source": "tool_audit"},
        )
        trace.span(
            name=f"tool:{tool_name}",
            input=arguments,
            output={
                "ok": result.get("ok"),
                "error": result.get("error"),
                "summary": str(result)[:1500],
            },
            metadata={
                "latency_ms": latency_ms,
                "success": bool(result.get("ok", False)),
                "tool_name": tool_name,
            },
        )
    except Exception:
        logger.exception("Failed to log tool span to Langfuse tool=%s", tool_name)


def finalize_agent_run_trace(
    *,
    request_id: str,
    query: str,
    answer: str,
    tools_used: list[str],
    latency_ms: int,
    prompt_name: str,
    prompt_version: int,
    user_sub: str,
    session_id: str,
    roles: list[str],
    pending_approvals: int,
) -> None:
    """Upsert the parent trace with full run I/O (complements LangChain callbacks)."""
    client = get_langfuse_client()
    if client is None:
        return
    try:
        client.trace(
            id=request_id,
            name="relay-agent-run",
            user_id=user_sub,
            session_id=session_id,
            input={"query": query},
            output={
                "answer": answer,
                "tools_used": tools_used,
                "pending_approvals": pending_approvals,
            },
            metadata={
                "latency_ms": latency_ms,
                "prompt_name": prompt_name,
                "prompt_version": prompt_version,
                "user_roles": roles,
                "product": "relay",
            },
            tags=["relay", "agent-run", *roles[:3]],
        )
        client.flush()
    except Exception:
        logger.exception("Failed to finalize Langfuse agent run trace")


def flush_langfuse_callbacks(callbacks: list[Any]) -> None:
    for callback in callbacks:
        flush = getattr(callback, "flush", None)
        if callable(flush):
            try:
                flush()
            except Exception:
                logger.exception("Langfuse callback flush failed")
