"""Build deep links into Relay observability UIs (Langfuse, LangSmith, etc.)."""

from __future__ import annotations

from typing import Any, Literal

from config import Settings, get_settings

ToolScope = Literal["event", "system"]


def build_langfuse_trace_url(
    request_id: str | None,
    settings: Settings | None = None,
) -> str | None:
    if not request_id:
        return None
    settings = settings or get_settings()
    if not settings.enable_langfuse:
        return None
    base = (settings.langfuse_ui_url or settings.langfuse_host or "").rstrip("/")
    if not base:
        return None
    project_id = (settings.langfuse_project_id or "").strip()
    if project_id:
        return f"{base}/project/{project_id}/traces/{request_id}"
    return f"{base}/traces/{request_id}"


def build_langsmith_run_url(
    run_id: str | None,
    settings: Settings | None = None,
) -> str | None:
    settings = settings or get_settings()
    if not settings.enable_langsmith:
        return None
    base = (settings.langsmith_ui_url or "").rstrip("/")
    if not base:
        return None
    if run_id and settings.langsmith_org_id and settings.langsmith_project:
        return (
            f"{base}/o/{settings.langsmith_org_id}"
            f"/projects/p/{settings.langsmith_project}/r/{run_id}"
        )
    if settings.langsmith_org_id and settings.langsmith_project:
        return (
            f"{base}/o/{settings.langsmith_org_id}"
            f"/projects/p/{settings.langsmith_project}"
        )
    return base


def build_glitchtip_url(settings: Settings | None = None) -> str | None:
    """GlitchTip is error-console scoped; link to the UI when configured."""
    settings = settings or get_settings()
    if not settings.enable_glitchtip:
        return None
    base = (settings.glitchtip_ui_url or "").rstrip("/")
    return base or None


def observability_catalog(settings: Settings | None = None) -> dict[str, Any]:
    """Catalog of auditability tools with direct open URLs for the Audit UI."""
    settings = settings or get_settings()
    langfuse_configured = bool(
        settings.enable_langfuse
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    )
    langsmith_configured = bool(
        settings.enable_langsmith and settings.langsmith_api_key
    )
    glitchtip_configured = bool(
        settings.enable_glitchtip
        and (settings.glitchtip_dsn or settings.glitchtip_ui_url)
    )

    tools = [
        {
            "id": "langfuse",
            "name": "Langfuse",
            "category": "LLM traces",
            "scope": "event",
            "description": (
                "Primary LLM/agent observability. Each agent run and tool call is "
                "mirrored here using request_id as the trace id."
            ),
            "enabled": settings.enable_langfuse,
            "configured": langfuse_configured,
            "ui_url": settings.langfuse_ui_url or settings.langfuse_host,
            "open_label": "Open Langfuse traces",
            "supports_per_event_link": True,
        },
        {
            "id": "langsmith",
            "name": "LangSmith",
            "category": "LLM traces",
            "scope": "event",
            "description": (
                "Optional LangChain/LangSmith project for run debugging. "
                "Enable with ENABLE_LANGSMITH + LANGSMITH_API_KEY when used."
            ),
            "enabled": settings.enable_langsmith,
            "configured": langsmith_configured,
            "ui_url": build_langsmith_run_url(None, settings)
            if settings.enable_langsmith
            else settings.langsmith_ui_url,
            "open_label": "Open LangSmith project",
            "supports_per_event_link": bool(settings.langsmith_org_id),
        },
        {
            "id": "glitchtip",
            "name": "GlitchTip",
            "category": "Error tracking",
            "scope": "event",
            "description": "Application exceptions and error events from the API/worker.",
            "enabled": settings.enable_glitchtip,
            "configured": glitchtip_configured,
            "ui_url": settings.glitchtip_ui_url,
            "open_label": "Open GlitchTip",
            "supports_per_event_link": True,
        },
        {
            "id": "grafana",
            "name": "Grafana",
            "category": "Metrics / dashboards",
            "scope": "system",
            "description": "Operational dashboards for Relay API and service health.",
            "enabled": True,
            "configured": bool(settings.grafana_ui_url),
            "ui_url": settings.grafana_ui_url,
            "open_label": "Open Grafana",
            "supports_per_event_link": False,
        },
        {
            "id": "postgres_audit",
            "name": "Postgres audit tables",
            "category": "Durable audit",
            "scope": "system",
            "description": (
                "Source of truth on this page: tool_call_audit, agent_runs, "
                "pending_approvals — always available without an external SaaS."
            ),
            "enabled": True,
            "configured": True,
            "ui_url": None,
            "open_label": "View on this page",
            "supports_per_event_link": False,
        },
    ]

    return {
        "langfuse_enabled": settings.enable_langfuse,
        "langfuse_configured": langfuse_configured,
        "langfuse_ui_url": settings.langfuse_ui_url or settings.langfuse_host,
        "langfuse_project_id": settings.langfuse_project_id,
        "langsmith_enabled": settings.enable_langsmith,
        "langsmith_configured": langsmith_configured,
        "langsmith_ui_url": settings.langsmith_ui_url,
        "glitchtip_enabled": settings.enable_glitchtip,
        "glitchtip_configured": glitchtip_configured,
        "glitchtip_ui_url": settings.glitchtip_ui_url,
        "tools": tools,
        "system_tools": [tool for tool in tools if tool["scope"] == "system"],
        "event_tools": [tool for tool in tools if tool["scope"] == "event"],
    }


def attach_observability_links(
    item: dict[str, Any],
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    request_id = item.get("request_id")
    item["langfuse_url"] = build_langfuse_trace_url(
        str(request_id) if request_id else None,
        settings,
    )
    item["langsmith_url"] = build_langsmith_run_url(
        str(request_id) if request_id else None,
        settings,
    )
    item["glitchtip_url"] = build_glitchtip_url(settings)
    return item
