from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from routers import approvals
from schemas.enums import Role


def _client_for(role: Role) -> TestClient:
    app = FastAPI()
    app.include_router(approvals.router)

    async def override_user() -> CurrentUser:
        return CurrentUser(
            sub=role.value,
            username=role.value,
            email=f"{role.value}@acme.local",
            roles={role},
        )

    app.dependency_overrides[get_current_user] = override_user
    return TestClient(app)


def test_list_approvals_includes_seeded_and_staged() -> None:
    client = _client_for(Role.SUPPORT)
    items = [
        {
            "approval_id": "na-1",
            "source": "next_actions",
            "issue_key": "OPS-3101",
            "action_text": "Bridge call",
            "owner": "Priya Nair",
            "tool": "create_next_action",
            "status": "pending",
        }
    ]
    with patch(
        "routers.approvals.list_pending_approvals",
        new=AsyncMock(return_value=items),
    ):
        response = client.get("/api/approvals")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["issue_key"] == "OPS-3101"


def test_stage_persists_via_store() -> None:
    client = _client_for(Role.SUPPORT)
    with patch(
        "routers.approvals.persist_staged_approvals",
        new=AsyncMock(return_value=["uuid-1"]),
    ) as persist:
        response = client.post(
            "/api/approvals/stage",
            json={
                "approval": {
                    "issue_key": "OPS-3101",
                    "action_text": "Bridge call",
                    "owner": "bob",
                }
            },
        )

    assert response.status_code == 200
    assert response.json()["approval_id"] == "uuid-1"
    persist.assert_awaited_once()


def test_decide_approves_next_action() -> None:
    client = _client_for(Role.ADMIN)
    with patch(
        "routers.approvals.decide_approval",
        new=AsyncMock(
            return_value={
                "ok": True,
                "status": "approved",
                "approval_id": "na-1",
                "next_action": {"id": "na-1", "status": "approved"},
            }
        ),
    ):
        response = client.post(
            "/api/approvals/decide",
            json={"approval_id": "na-1", "approve": True},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_decide_missing_returns_404() -> None:
    client = _client_for(Role.ADMIN)
    with patch(
        "routers.approvals.decide_approval",
        new=AsyncMock(return_value={"ok": False, "error": "Approval not found"}),
    ):
        response = client.post(
            "/api/approvals/decide",
            json={"approval_id": "missing", "approve": False},
        )

    assert response.status_code == 404
