from typing import Annotated, Any

from fastapi import APIRouter, Depends

from auth.dependencies import CurrentUser, require_permission
from support.db import acquire

router = APIRouter(prefix="/api/desk", tags=["desk"])


@router.get("/summary")
async def desk_summary(
    user: Annotated[CurrentUser, Depends(require_permission("read_issues"))],
) -> dict[str, Any]:
    async with acquire() as connection:
        open_count = await connection.fetchval(
            "SELECT count(*) FROM issues WHERE status IN ('open', 'in_progress')"
        )
        critical_count = await connection.fetchval(
            "SELECT count(*) FROM issues WHERE status IN ('open', 'in_progress') AND priority = 'critical'"
        )
        pending_actions = await connection.fetchval(
            "SELECT count(*) FROM next_actions WHERE status = 'pending'"
        )
        customers = await connection.fetchval(
            "SELECT count(*) FROM customers WHERE is_active"
        )
        sla_breach_risk = await connection.fetchval(
            """
            SELECT count(*) FROM issues
            WHERE status IN ('open', 'in_progress')
              AND sla_due_at IS NOT NULL
              AND sla_due_at < now() + interval '4 hours'
            """
        )
        open_tasks = await connection.fetchval(
            "SELECT count(*) FROM user_tasks WHERE status = 'open'"
        )
        groundedness_pass_rate = await connection.fetchval(
            """
            SELECT CASE WHEN count(*) = 0 THEN NULL
                   ELSE round(100.0 * count(*) FILTER (WHERE groundedness_passed) / count(*), 1)
                   END
            FROM agent_runs
            WHERE groundedness_passed IS NOT NULL
              AND created_at > now() - interval '7 days'
            """
        )
    return {
        "open_cases": open_count,
        "critical_cases": critical_count,
        "pending_actions": pending_actions,
        "active_accounts": customers,
        "sla_breach_risk": sla_breach_risk or 0,
        "open_tasks": open_tasks or 0,
        "groundedness_pass_rate_7d": groundedness_pass_rate,
        "role_scope": sorted(role.value for role in user.roles),
    }


@router.get("/accounts")
async def list_accounts(
    user: Annotated[CurrentUser, Depends(require_permission("read_customer"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT external_id, name, industry, tier, account_owner, region
            FROM customers
            WHERE is_active
            ORDER BY name
            """
        )
    return {"items": [dict(row) for row in rows]}


@router.get("/cases")
async def list_cases(
    user: Annotated[CurrentUser, Depends(require_permission("read_issues"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT i.issue_key, i.title, i.status::text, i.priority::text,
                   i.assigned_to, c.name AS customer_name, c.external_id
            FROM issues i
            JOIN customers c ON c.id = i.customer_id
            ORDER BY i.updated_at DESC
            LIMIT 100
            """
        )
    return {"items": [dict(row) for row in rows]}
