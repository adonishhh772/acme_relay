from typing import Any

from agent.tools import ToolContext, get_open_issues, summarize_issue_history


async def run_shift_handoff(ctx: ToolContext, customer_name: str) -> dict[str, Any]:
    open_issues = await get_open_issues(ctx, customer_name)
    if not open_issues.get("ok"):
        return open_issues
    bullets: list[str] = []
    for issue in (open_issues.get("open_issues") or [])[:5]:
        history = await summarize_issue_history(ctx, issue["issue_key"])
        latest = ""
        updates = history.get("updates") or []
        if updates:
            latest = updates[-1]["body"]
        bullets.append(
            f"{issue['issue_key']} [{issue['priority']}] owner={issue.get('assigned_to') or 'unassigned'} — {latest}"
        )
    return {
        "ok": True,
        "skill": "shift_handoff_briefing",
        "customer_query": customer_name,
        "handoff_bullets": bullets,
        "summary": f"Handoff pack for {customer_name}: {len(bullets)} active thread(s).",
    }
