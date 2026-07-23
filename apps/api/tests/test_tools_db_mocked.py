from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from agent import tools
from agent.tools import (
    ToolContext,
    get_customer_profile_by_name,
    get_open_issues,
    summarize_issue_history,
    update_issue,
)
from schemas.enums import Role
from skills import escalation, handoff, sla, triage
from skills.registry import invoke_skill


class FakeConn:
    def __init__(self, fetchrow=None, fetch=None, fetchval=None, execute=None):
        self.fetchrow = AsyncMock(return_value=fetchrow)
        self.fetch = AsyncMock(return_value=fetch or [])
        self.fetchval = AsyncMock(return_value=fetchval)
        self.execute = AsyncMock(return_value=execute)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def transaction(self):
        return self


class FakeAcquire:
    def __init__(self, conn: FakeConn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, *args):
        return False


@pytest.fixture
def support_ctx() -> ToolContext:
    return ToolContext(
        user_sub="bob", username="bob", roles={Role.SUPPORT}, session_id="s"
    )


@pytest.mark.asyncio
async def test_get_customer_profile(
    monkeypatch: pytest.MonkeyPatch, support_ctx: ToolContext
) -> None:
    row = {
        "external_id": "VAULTLEDGER",
        "name": "VaultLedger Payments",
        "industry": "Fintech",
        "tier": "strategic",
        "account_owner": "Priya",
        "region": "EMEA",
    }
    monkeypatch.setattr(tools, "acquire", lambda: FakeAcquire(FakeConn(fetchrow=row)))
    result = await get_customer_profile_by_name(support_ctx, "VaultLedger")
    assert result["ok"] is True
    assert result["customer"]["external_id"] == "VAULTLEDGER"


@pytest.mark.asyncio
async def test_get_open_issues(
    monkeypatch: pytest.MonkeyPatch, support_ctx: ToolContext
) -> None:
    rows = [
        {
            "issue_key": "OPS-3101",
            "title": "x",
            "status": "open",
            "priority": "critical",
            "assigned_to": "bob",
            "sla_due_at": datetime.now(timezone.utc),
            "customer_name": "VaultLedger Payments",
            "external_id": "VAULTLEDGER",
        }
    ]
    monkeypatch.setattr(tools, "acquire", lambda: FakeAcquire(FakeConn(fetch=rows)))
    result = await get_open_issues(support_ctx, "VaultLedger")
    assert result["count"] == 1


@pytest.mark.asyncio
async def test_summarize_filters_internal_for_sales(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = ToolContext(user_sub="a", username="a", roles={Role.SALES}, session_id="s")
    issue = {
        "issue_key": "OPS-3101",
        "title": "t",
        "status": "open",
        "priority": "high",
        "description": "d",
        "customer_name": "VaultLedger Payments",
    }
    updates = [
        {
            "author": "bob",
            "body": "public",
            "is_internal": False,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "author": "sys",
            "body": "secret",
            "is_internal": True,
            "created_at": datetime.now(timezone.utc),
        },
    ]
    conn = FakeConn(fetchrow=issue, fetch=updates)
    monkeypatch.setattr(tools, "acquire", lambda: FakeAcquire(conn))
    result = await summarize_issue_history(ctx, "OPS-3101")
    assert result["ok"] is True
    assert len(result["updates"]) == 1


@pytest.mark.asyncio
async def test_update_issue_hitl(support_ctx: ToolContext) -> None:
    result = await update_issue(
        support_ctx, "OPS-3101", status="in_progress", comment="working"
    )
    assert result["pending_approval"] is True


@pytest.mark.asyncio
async def test_escalation_skill(
    monkeypatch: pytest.MonkeyPatch, support_ctx: ToolContext
) -> None:
    async def fake_profile(ctx, name):
        return {
            "ok": True,
            "customer": {
                "name": "VaultLedger Payments",
                "external_id": "VAULTLEDGER",
                "account_owner": "Priya",
            },
        }

    async def fake_open(ctx, name):
        return {
            "ok": True,
            "open_issues": [
                {"issue_key": "OPS-3101", "priority": "critical", "assigned_to": "bob"}
            ],
        }

    async def fake_hist(ctx, key):
        return {"ok": True, "updates": [{"body": "latest"}]}

    monkeypatch.setattr(escalation, "get_customer_profile_by_name", fake_profile)
    monkeypatch.setattr(escalation, "get_open_issues", fake_open)
    monkeypatch.setattr(escalation, "summarize_issue_history", fake_hist)
    result = await invoke_skill(support_ctx, "run_escalation_summary_skill", "VaultLedger")
    assert result["ok"] is True
    assert result["risk_level"] == "Critical"


@pytest.mark.asyncio
async def test_sla_skill(
    monkeypatch: pytest.MonkeyPatch, support_ctx: ToolContext
) -> None:
    async def fake_open(ctx, name):
        return {
            "ok": True,
            "open_issues": [
                {
                    "issue_key": "OPS-3101",
                    "priority": "critical",
                    "sla_due_at": datetime.now(timezone.utc),
                }
            ],
        }

    monkeypatch.setattr(sla, "get_open_issues", fake_open)
    result = await invoke_skill(
        support_ctx, "run_sla_breach_assessment_skill", "VaultLedger"
    )
    assert result["ok"] is True


@pytest.mark.asyncio
async def test_triage_and_handoff(
    monkeypatch: pytest.MonkeyPatch, support_ctx: ToolContext
) -> None:
    async def fake_open(ctx, name):
        return {
            "ok": True,
            "open_issues": [
                {
                    "issue_key": "OPS-3101",
                    "title": "t",
                    "priority": "high",
                    "assigned_to": "bob",
                }
            ],
        }

    async def fake_hist(ctx, key):
        return {"ok": True, "updates": [{"body": "note"}]}

    monkeypatch.setattr(triage, "get_open_issues", fake_open)
    monkeypatch.setattr(handoff, "get_open_issues", fake_open)
    monkeypatch.setattr(handoff, "summarize_issue_history", fake_hist)
    triage_result = await invoke_skill(
        support_ctx, "run_issue_triage_skill", "VaultLedger"
    )
    handoff_result = await invoke_skill(
        support_ctx, "run_shift_handoff_skill", "VaultLedger"
    )
    assert triage_result["ok"] is True
    assert handoff_result["ok"] is True


@pytest.mark.asyncio
async def test_unknown_skill_name(support_ctx: ToolContext) -> None:
    from skills.registry import SKILLS

    support_ctx.roles = {Role.ADMIN}
    assert "not_a_real_skill" not in SKILLS
