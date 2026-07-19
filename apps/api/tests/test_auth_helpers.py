import pytest
from fastapi import HTTPException

from auth.dependencies import CurrentUser, get_current_user
from auth.rbac import roles_for_knowledge_filter, roles_from_claims, tool_allowed
from config import Settings
from schemas.enums import Role


def test_roles_from_claims() -> None:
    roles = roles_from_claims(["sales_user", "unknown", "admin"])
    assert Role.SALES in roles
    assert Role.ADMIN in roles


def test_roles_for_knowledge_filter() -> None:
    assert "support_user" in roles_for_knowledge_filter({Role.SUPPORT})


def test_tool_allowed_default_admin_only() -> None:
    assert tool_allowed({Role.ADMIN}, "totally_unknown_tool")
    assert not tool_allowed({Role.SALES}, "totally_unknown_tool")


@pytest.mark.asyncio
async def test_get_current_user_test_mode() -> None:
    settings = Settings(auth_disabled_for_tests=True)
    user = await get_current_user(None, settings)
    assert Role.ADMIN in user.roles


@pytest.mark.asyncio
async def test_get_current_user_missing_token() -> None:
    settings = Settings(auth_disabled_for_tests=False)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None, settings)
    assert exc.value.status_code == 401


def test_current_user_can() -> None:
    user = CurrentUser(sub="1", username="a", email="a", roles={Role.SALES})
    assert user.can("read_customer")
    assert not user.can("approve_next_action")
