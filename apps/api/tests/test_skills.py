import pytest

from agent.tools import ToolContext
from skills.escalation import _score_risk
from skills.registry import invoke_skill


def test_score_risk_critical() -> None:
    assert _score_risk([{"priority": "critical"}]).value == "Critical"


@pytest.mark.asyncio
async def test_skill_denied_for_empty_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = ToolContext(user_sub="x", username="x", roles=set(), session_id="s")
    result = await invoke_skill(ctx, "run_escalation_summary_skill", "VaultLedger")
    assert result["error"] == "permission_denied"
