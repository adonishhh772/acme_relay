from collections.abc import Awaitable, Callable
from typing import Any

from agent.tools import ToolContext
from auth.rbac import tool_allowed
from skills.escalation import run_escalation_summary
from skills.handoff import run_shift_handoff
from skills.sla import run_sla_breach_assessment
from skills.triage import run_issue_triage

SkillFn = Callable[[ToolContext, str], Awaitable[dict[str, Any]]]

SKILLS: dict[str, SkillFn] = {
    "run_escalation_summary_skill": run_escalation_summary,
    "run_sla_breach_assessment_skill": run_sla_breach_assessment,
    "run_issue_triage_skill": run_issue_triage,
    "run_shift_handoff_skill": run_shift_handoff,
}


async def invoke_skill(
    ctx: ToolContext, skill_name: str, customer_name: str
) -> dict[str, Any]:
    if not tool_allowed(ctx.roles, skill_name):
        return {
            "ok": False,
            "error": "permission_denied",
            "tool": skill_name,
            "message": f"Your role cannot use {skill_name}.",
        }
    handler = SKILLS.get(skill_name)
    if handler is None:
        return {"ok": False, "error": "unknown_skill", "skill": skill_name}
    return await handler(ctx, customer_name)
