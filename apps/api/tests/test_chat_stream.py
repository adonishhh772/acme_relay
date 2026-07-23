from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from routers.chat import router
from schemas.chat import ChatResponse, GroundednessPayload
from schemas.enums import Role


@pytest.fixture
def stream_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)

    async def fake_user() -> CurrentUser:
        return CurrentUser(
            sub="bob",
            username="bob",
            email="bob@example.com",
            roles={Role.SUPPORT},
        )

    app.dependency_overrides[get_current_user] = fake_user
    return TestClient(app)


def test_chat_stream_emits_started_progress_done(stream_client: TestClient) -> None:
    fake_response = ChatResponse(
        answer="OPS-3101 is critical.",
        session_id="sess",
        request_id="req",
        tools_used=["get_open_issues"],
        pending_approvals=[],
        prompt_name="relay-system",
        prompt_version=1,
        latency_ms=12,
        grounded=True,
        groundedness=GroundednessPayload(
            passed=True,
            unsupported_claims=[],
            evidence_ids_used=["OPS-3101"],
            explanation="Aligned with tools",
        ),
    )

    async def fake_run_chat_turn(body, user, *, progress=None, request_id=None):
        if progress is not None:
            await progress.emit("tool_start", tool="get_open_issues", source="native")
            await progress.emit(
                "tool_done",
                tool="get_open_issues",
                source="native",
                latency_ms=3,
                status="ok",
            )
        return fake_response.model_copy(update={"request_id": request_id or "req"})

    with patch("routers.chat.run_chat_turn", new=AsyncMock(side_effect=fake_run_chat_turn)):
        with stream_client.stream(
            "POST",
            "/api/chat/stream",
            json={"query": "VaultLedger status?"},
        ) as response:
            assert response.status_code == 200
            body = "".join(response.iter_text())

    assert "event: started" in body
    assert "event: progress" in body
    assert "event: done" in body
    assert "OPS-3101" in body
    assert '"grounded": true' in body or '"grounded":true' in body
