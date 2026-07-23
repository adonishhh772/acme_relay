"""Admin MFA require/disable routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from auth.keycloak_admin import KeycloakUserSummary
from routers.admin import router
from schemas.enums import Role


def _admin() -> CurrentUser:
    return CurrentUser(
        sub="admin",
        username="admin",
        email="admin@acme.local",
        roles={Role.ADMIN},
    )


def _summary(**overrides: object) -> KeycloakUserSummary:
    base = KeycloakUserSummary(
        id="kc-bob",
        username="bob",
        email="bob@acme.test",
        first_name="Bob",
        last_name="Support",
        email_verified=True,
        roles=["support_user"],
        totp_configured=False,
        required_actions=[],
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = _admin
    return TestClient(app)


def test_admin_require_2fa() -> None:
    kc = MagicMock()
    kc.require_totp_setup = AsyncMock(
        return_value=_summary(required_actions=["CONFIGURE_TOTP"])
    )
    client = _client()
    with patch("routers.admin.get_keycloak_admin_client", return_value=kc):
        response = client.post("/api/admin/users/kc-bob/require-2fa")
    assert response.status_code == 200
    body = response.json()
    assert body["mfa_setup_pending"] is True
    kc.require_totp_setup.assert_awaited_once_with("kc-bob")


def test_admin_disable_2fa() -> None:
    kc = MagicMock()
    kc.disable_totp = AsyncMock(return_value=_summary(totp_configured=False))
    client = _client()
    with patch("routers.admin.get_keycloak_admin_client", return_value=kc):
        response = client.post("/api/admin/users/kc-bob/disable-2fa")
    assert response.status_code == 200
    body = response.json()
    assert body["totp_configured"] is False
    kc.disable_totp.assert_awaited_once_with("kc-bob")


def test_admin_list_users_includes_mfa_status() -> None:
    connection = MagicMock()
    connection.fetch = AsyncMock(
        return_value=[
            {
                "id": "1",
                "email": "bob@acme.test",
                "display_name": "Bob",
                "role": "support_user",
                "is_active": True,
                "keycloak_sub": "kc-bob",
                "organization_slug": "acme-ops",
                "organization_name": "Acme Operations",
            }
        ]
    )
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=connection)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    kc = MagicMock()
    kc.sync_totp_state = AsyncMock(
        return_value=_summary(totp_configured=True, required_actions=[])
    )

    client = _client()
    with (
        patch("routers.admin.acquire", return_value=acquire_cm),
        patch("routers.admin.get_keycloak_admin_client", return_value=kc),
    ):
        response = client.get("/api/admin/users")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["totp_configured"] is True
    assert item["mfa_setup_pending"] is False
