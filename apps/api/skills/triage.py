from typing import Any

from agent.tools import ToolContext, get_open_issues

PRIORITY_WEIGHT = {"critical": 40, "high": 25, "medium": 10, "low": 5}


async def run_issue_triage(ctx: ToolContext, customer_name: str) -> dict[str, Any]:
    open_issues = await get_open_issues(ctx, customer_name)
    if not open_issues.get("ok"):
        return open_issues
    ranked = []
    for issue in open_issues.get("open_issues") or []:
        score = PRIORITY_WEIGHT.get(str(issue.get("priority")), 5)
        ranked.append(
            {
                "issue_key": issue["issue_key"],
                "title": issue["title"],
                "priority": issue["priority"],
                "triage_score": score,
                "suggested_queue": "critical-bridge"
                if score >= 40
                else "standard-support",
            }
        )
    ranked.sort(key=lambda item: item["triage_score"], reverse=True)
    return {
        "ok": True,
        "skill": "issue_triage",
        "ranked_issues": ranked,
        "summary": f"Triaged {len(ranked)} open case(s) for {customer_name}.",
    }
