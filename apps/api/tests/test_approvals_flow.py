from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from main import app
from schemas.enums import Role


def test_stage_and_list_approvals() -> None:
    async def override_user() -> CurrentUser:
        return CurrentUser(sub="bob", username="bob", email="b@x", roles={Role.SUPPORT})

    app.dependency_overrides[get_current_user] = override_user
    client = TestClient(app)
    stage = client.post(
        "/api/approvals/stage",
        json={
            "approval": {
                "approval_id": "appr-1",
                "issue_key": "CASE-2001",
                "action_text": "Bridge call",
                "owner": "bob",
            }
        },
    )
    listed = client.get("/api/approvals")
    app.dependency_overrides.clear()
    assert stage.status_code == 200
    assert listed.status_code == 200
    assert any(item["approval_id"] == "appr-1" for item in listed.json()["items"])
