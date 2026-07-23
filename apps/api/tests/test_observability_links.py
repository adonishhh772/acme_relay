"""Tests for observability deep-link helpers."""

from __future__ import annotations

from config import Settings
from services.observability_links import (
    attach_observability_links,
    build_glitchtip_url,
    build_langfuse_trace_url,
    observability_catalog,
)


def test_build_langfuse_trace_url_with_project() -> None:
    settings = Settings(
        enable_langfuse=True,
        langfuse_ui_url="http://localhost:3001",
        langfuse_project_id="relay-ops",
    )
    url = build_langfuse_trace_url("abc-123", settings)
    assert url == "http://localhost:3001/project/relay-ops/traces/abc-123"


def test_build_glitchtip_url_when_enabled() -> None:
    settings = Settings(
        enable_glitchtip=True,
        glitchtip_ui_url="http://localhost:8001",
    )
    assert build_glitchtip_url(settings) == "http://localhost:8001"


def test_build_glitchtip_url_when_disabled() -> None:
    settings = Settings(
        enable_glitchtip=False,
        glitchtip_ui_url="http://localhost:8001",
    )
    assert build_glitchtip_url(settings) is None


def test_observability_catalog_includes_core_tools() -> None:
    settings = Settings(
        enable_langfuse=True,
        langfuse_public_key="pk",
        langfuse_secret_key="sk",
        langfuse_ui_url="http://localhost:3001",
        grafana_ui_url="http://localhost:3002",
        enable_glitchtip=True,
        glitchtip_ui_url="http://localhost:8001",
    )
    catalog = observability_catalog(settings)
    ids = {tool["id"] for tool in catalog["tools"]}
    assert {
        "langfuse",
        "langsmith",
        "grafana",
        "glitchtip",
        "postgres_audit",
    }.issubset(ids)
    assert "prometheus" not in ids
    langfuse = next(tool for tool in catalog["tools"] if tool["id"] == "langfuse")
    assert langfuse["configured"] is True
    assert langfuse["ui_url"] == "http://localhost:3001"
    assert langfuse["scope"] == "event"
    system_ids = {tool["id"] for tool in catalog["system_tools"]}
    assert system_ids == {"grafana", "postgres_audit"}
    event_ids = {tool["id"] for tool in catalog["event_tools"]}
    assert "langfuse" in event_ids
    assert "glitchtip" in event_ids
    assert "grafana" not in event_ids


def test_attach_observability_links_adds_langfuse_and_glitchtip() -> None:
    settings = Settings(
        enable_langfuse=True,
        langfuse_ui_url="http://localhost:3001",
        langfuse_project_id="relay-ops",
        enable_langsmith=False,
        enable_glitchtip=True,
        glitchtip_ui_url="http://localhost:8001",
    )
    item = attach_observability_links({"request_id": "req-9"}, settings)
    assert item["langfuse_url"] == "http://localhost:3001/project/relay-ops/traces/req-9"
    assert item["langsmith_url"] is None
    assert item["glitchtip_url"] == "http://localhost:8001"
