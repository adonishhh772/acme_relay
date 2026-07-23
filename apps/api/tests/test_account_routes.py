"""Tests for account profile / MFA routes backed by Keycloak admin client."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from auth.keycloak_admin import KeycloakUserSummary
from main import app
from schemas.enums import Role


def _user() -> CurrentUser:
    return CurrentUser(
        sub="user-1",
        username="bob",
        email="bob@acme.test",
        roles={Role.SUPPORT},
    )


def _summary(**overrides: object) -> KeycloakUserSummary:
    base = KeycloakUserSummary(
        id="user-1",
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


@asynccontextmanager
async def _fake_acquire():
    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        return_value={"slug": "acme-ops", "display_name": "Acme Operations"}
    )
    yield connection


def test_update_profile_via_keycloak_admin() -> None:
    client_mock = MagicMock()
    client_mock.update_user = AsyncMock(
        return_value=_summary(first_name="Robert", email="robert@acme.test")
    )

    app.dependency_overrides[get_current_user] = _user
    with (
        patch("routers.account.get_keycloak_admin_client", return_value=client_mock),
        patch("routers.account.acquire", _fake_acquire),
        TestClient(app) as client,
    ):
        response = client.patch(
            "/api/account/profile",
            json={
                "first_name": "Robert",
                "last_name": "Support",
                "email": "robert@acme.test",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Robert"
    assert body["email"] == "robert@acme.test"
    client_mock.update_user.assert_awaited_once()


def test_change_password_verifies_current() -> None:
    client_mock = MagicMock()
    client_mock.get_user = AsyncMock(return_value=_summary())
    client_mock.verify_user_password = AsyncMock(return_value=True)
    client_mock.reset_user_password = AsyncMock()

    app.dependency_overrides[get_current_user] = _user
    with (
        patch("routers.account.get_keycloak_admin_client", return_value=client_mock),
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/account/password",
            json={"current_password": "bob123", "new_password": "newpassword1"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 204
    client_mock.reset_user_password.assert_awaited_once()


def test_require_2fa_flags_configure_totp() -> None:
    client_mock = MagicMock()
    client_mock.require_totp_setup = AsyncMock(
        return_value=_summary(required_actions=["CONFIGURE_TOTP"])
    )

    app.dependency_overrides[get_current_user] = _user
    with (
        patch("routers.account.get_keycloak_admin_client", return_value=client_mock),
        TestClient(app) as client,
    ):
        response = client.post("/api/account/require-2fa")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["setup_pending"] is True
    assert "CONFIGURE_TOTP" in body["required_actions"]


def test_security_status_reports_totp() -> None:
    client_mock = MagicMock()
    client_mock.sync_totp_state = AsyncMock(
        return_value=_summary(totp_configured=True, required_actions=[])
    )

    app.dependency_overrides[get_current_user] = _user
    with (
        patch("routers.account.get_keycloak_admin_client", return_value=client_mock),
        TestClient(app) as client,
    ):
        response = client.get("/api/account/security")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["totp_configured"] is True
    assert body["setup_pending"] is False
    assert "account_console_url" not in body
