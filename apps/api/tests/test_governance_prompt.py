from fastapi.testclient import TestClient

from auth.dependencies import get_current_user
from auth.dependencies import CurrentUser
from main import app
from schemas.enums import Role


def test_governance_prompts_admin() -> None:
    async def override_user() -> CurrentUser:
        return CurrentUser(sub="a", username="a", email="a@x", roles={Role.ADMIN})

    app.dependency_overrides[get_current_user] = override_user
    client = TestClient(app)
    response = client.get("/api/governance/prompts")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["active"]["name"] == "relay/system"
