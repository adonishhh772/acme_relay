"""Audit API unit tests (permission + response shape)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from routers.audit import router
from schemas.enums import Role


@pytest.fixture
def audit_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)

    async def fake_ops() -> CurrentUser:
        return CurrentUser(
            sub="dana-ops",
            username="dana",
            email="dana@acme.local",
            roles={Role.OPERATIONS},
        )

    app.dependency_overrides[get_current_user] = fake_ops
    return TestClient(app)


def test_audit_summary_describes_streams(audit_client: TestClient) -> None:
    tool_stats = {
        "total_tool_calls": 4,
        "tool_successes": 3,
        "tool_failures": 1,
        "mcp_calls": 1,
        "native_calls": 3,
        "avg_tool_latency_ms": 12.5,
    }
    run_stats = {
        "total_runs": 2,
        "grounded_pass": 2,
        "grounded_fail": 0,
        "avg_run_latency_ms": 400.0,
    }
    approval_stats = {"pending": 1, "approved": 0, "rejected": 0}

    connection = MagicMock()
    connection.fetchrow = AsyncMock(side_effect=[tool_stats, run_stats, approval_stats])
    connection.fetch = AsyncMock(
        return_value=[{"tool_name": "get_open_issues", "calls": 3}]
    )

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=connection)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("routers.audit.acquire", return_value=cm):
        response = audit_client.get("/api/audit/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["tool_calls_7d"] == 4
    assert body["groundedness_pass_rate_7d"] == 100.0
    assert len(body["what_we_audit"]) == 3
    assert {item["table"] for item in body["what_we_audit"]} == {
        "tool_call_audit",
        "agent_runs",
        "pending_approvals",
    }
    assert "observability" in body
    assert any(tool["id"] == "langfuse" for tool in body["observability"]["tools"])
