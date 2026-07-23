from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from routers.admin import router
from schemas.enums import Role


@pytest.fixture
def admin_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)

    async def fake_admin() -> CurrentUser:
        return CurrentUser(
            sub="admin",
            username="admin",
            email="admin@acme.local",
            roles={Role.ADMIN},
        )

    app.dependency_overrides[get_current_user] = fake_admin
    return TestClient(app)


def test_rbac_matrix_returns_roles_and_permissions(admin_client: TestClient) -> None:
    permission_rows = [
        {"key": "read_customer", "description": "View customers", "category": "customers"},
        {"key": "manage_users", "description": "Manage users", "category": "admin"},
    ]
    role_rows = [
        {
            "slug": "sales_user",
            "name": "Sales User",
            "keycloak_role_name": "sales_user",
            "is_system": True,
            "permission_keys": ["read_customer"],
        }
    ]

    connection = MagicMock()
    connection.fetch = AsyncMock(side_effect=[permission_rows, role_rows])
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=connection)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("routers.admin.acquire", return_value=acquire_cm):
        response = admin_client.get("/api/admin/rbac-matrix")

    assert response.status_code == 200
    body = response.json()
    assert body["permissions"][0]["key"] == "read_customer"
    assert body["roles"][0]["slug"] == "sales_user"
    assert "read_customer" in body["runtime_permissions"]


def test_update_user_rejects_invalid_role(admin_client: TestClient) -> None:
    connection = MagicMock()
    connection.fetchrow = AsyncMock(return_value={"email": "bob@acme.local"})
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=connection)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("routers.admin.acquire", return_value=acquire_cm):
        response = admin_client.patch(
            "/api/admin/users/bob@acme.local",
            json={"role": "superuser"},
        )

    assert response.status_code == 400
