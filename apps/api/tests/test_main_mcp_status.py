from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from config import get_settings
from main import app
from schemas.enums import Role


def test_mcp_status_returns_server_matrix() -> None:
    get_settings.cache_clear()

    async def fake_user() -> CurrentUser:
        return CurrentUser(
            sub="admin",
            username="admin",
            email="admin@example.com",
            roles={Role.ADMIN},
        )

    app.dependency_overrides[get_current_user] = fake_user

    response_obj = MagicMock()
    response_obj.status_code = 200
    stream_cm = AsyncMock()
    stream_cm.__aenter__.return_value = response_obj
    stream_cm.__aexit__.return_value = None

    client_instance = MagicMock()
    client_instance.stream.return_value = stream_cm
    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client_instance
    client_cm.__aexit__.return_value = None

    with (
        patch("main.init_pool", new=AsyncMock()),
        patch("main.close_pool", new=AsyncMock()),
        patch("main.warm_mcp_tools", new=AsyncMock()),
        patch("main.configure_observability"),
        patch("main.httpx.AsyncClient", return_value=client_cm),
        patch(
            "main.mcp_load_status",
            return_value={
                "enabled": True,
                "loaded": True,
                "tool_count": 4,
                "error": None,
                "tool_names": ["domain_relay_list_open_issues"],
            },
        ),
    ):
        with TestClient(app) as test_client:
            response = test_client.get("/api/mcp/status")

    app.dependency_overrides.clear()
    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["agent_tools_enabled"] is True
    assert body["agent_tool_count"] == 4
    assert len(body["servers"]) == 3
    assert all(server["reachable"] for server in body["servers"])
