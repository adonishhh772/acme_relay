import pytest

from agent.tools import ToolContext, _denied, create_next_action, search_knowledge
from schemas.enums import Role


def test_denied_payload() -> None:
    payload = _denied("create_next_action")
    assert payload["error"] == "permission_denied"


@pytest.mark.asyncio
async def test_sales_create_next_action_denied() -> None:
    ctx = ToolContext(
        user_sub="alice",
        username="alice",
        roles={Role.SALES},
        session_id="s1",
    )
    result = await create_next_action(ctx, "OPS-3101", "Call customer")
    assert result["error"] == "permission_denied"


@pytest.mark.asyncio
async def test_support_create_next_action_stages_hitl() -> None:
    ctx = ToolContext(
        user_sub="bob",
        username="bob",
        roles={Role.SUPPORT},
        session_id="s1",
    )
    result = await create_next_action(ctx, "OPS-3101", "Call customer", owner="bob")
    assert result["ok"] is True
    assert result["pending_approval"] is True
    assert len(ctx.pending_approvals) == 1


@pytest.mark.asyncio
async def test_search_knowledge_denied_without_roles() -> None:
    ctx = ToolContext(user_sub="x", username="x", roles=set(), session_id="s")
    result = await search_knowledge(ctx, "sla")
    assert result["error"] == "permission_denied"
