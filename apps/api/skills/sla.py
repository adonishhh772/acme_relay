from datetime import datetime, timezone
from typing import Any

from agent.tools import ToolContext, get_open_issues


async def run_sla_breach_assessment(
    ctx: ToolContext, customer_name: str
) -> dict[str, Any]:
    open_issues = await get_open_issues(ctx, customer_name)
    if not open_issues.get("ok"):
        return open_issues
    now = datetime.now(timezone.utc)
    at_risk: list[dict[str, Any]] = []
    for issue in open_issues.get("open_issues") or []:
        due = issue.get("sla_due_at")
        if due is None:
            continue
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        hours_left = (due - now).total_seconds() / 3600.0
        if hours_left <= 4:
            at_risk.append(
                {
                    "issue_key": issue["issue_key"],
                    "priority": issue["priority"],
                    "hours_remaining": round(hours_left, 2),
                    "status": "breached" if hours_left < 0 else "imminent",
                }
            )
    return {
        "ok": True,
        "skill": "sla_breach_assessment",
        "customer_query": customer_name,
        "at_risk_issues": at_risk,
        "summary": f"{len(at_risk)} case(s) breached or within 4h of SLA.",
    }
