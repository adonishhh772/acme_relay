from typing import Any

from agent.tools import (
    ToolContext,
    get_customer_profile_by_name,
    get_open_issues,
    summarize_issue_history,
)
from schemas.enums import RiskLevel


def _score_risk(issues: list[dict[str, Any]]) -> RiskLevel:
    priorities = {item.get("priority") for item in issues}
    if "critical" in priorities:
        return RiskLevel.CRITICAL
    if "high" in priorities:
        return RiskLevel.HIGH
    if len(issues) >= 3:
        return RiskLevel.MEDIUM
    if issues:
        return RiskLevel.LOW
    return RiskLevel.LOW


async def run_escalation_summary(
    ctx: ToolContext, customer_name: str
) -> dict[str, Any]:
    profile = await get_customer_profile_by_name(ctx, customer_name)
    if not profile.get("ok"):
        return profile
    open_issues = await get_open_issues(ctx, customer_name)
    issues = open_issues.get("open_issues") or []
    histories: list[dict[str, Any]] = []
    for issue in issues[:5]:
        history = await summarize_issue_history(ctx, issue["issue_key"])
        if history.get("ok"):
            histories.append(history)

    risk = _score_risk(issues)
    missing: list[str] = []
    if not issues:
        missing.append("No open issues found — confirm customer name.")
    if not any((history.get("updates") for history in histories)):
        missing.append("Limited update history for open cases.")

    recommended = (
        f"Brief account owner {profile['customer'].get('account_owner')} on {len(issues)} open case(s) "
        f"and confirm mitigation owners for highest-priority items."
    )
    if issues:
        top = issues[0]
        recommended = (
            f"Prioritise {top['issue_key']} ({top['priority']}): align owner {top.get('assigned_to') or 'unassigned'} "
            f"and propose a customer-facing next action for approval."
        )

    executive_summary = (
        f"{profile['customer']['name']} ({profile['customer']['external_id']}) has {len(issues)} open case(s). "
        f"Risk assessed as {risk.value}. Account owner: {profile['customer'].get('account_owner')}."
    )
    return {
        "ok": True,
        "skill": "customer_escalation_summary",
        "customer": profile["customer"],
        "open_issues": issues,
        "histories": histories,
        "executive_summary": executive_summary,
        "risk_level": risk.value,
        "recommended_next_action": recommended,
        "missing_information": missing,
    }
