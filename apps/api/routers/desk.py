from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import CurrentUser, require_permission
from services.desk_am import fetch_account_risk_items, summarize_account_risk
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
        risk_items = await fetch_account_risk_items(connection)
        risk_summary = summarize_account_risk(risk_items)

        by_priority = await connection.fetch(
            """
            SELECT priority::text AS label, count(*)::int AS value
            FROM issues
            WHERE status IN ('open', 'in_progress')
            GROUP BY priority
            ORDER BY CASE priority
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
            """
        )
        by_status = await connection.fetch(
            """
            SELECT status::text AS label, count(*)::int AS value
            FROM issues
            WHERE status IN ('open', 'in_progress', 'resolved')
            GROUP BY status
            ORDER BY status
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
        "customers_at_risk": risk_summary["total_at_risk"],
        "customers_high_risk": risk_summary["total_high_risk"],
        "renewals_at_risk": risk_summary["renewals_at_risk"],
        "contract_value_at_risk_gbp": risk_summary["contract_value_at_risk_gbp"],
        "charts": {
            "by_priority": [dict(row) for row in by_priority],
            "by_status": [dict(row) for row in by_status],
            "risk_by_account": [
                {
                    "label": item["name"],
                    "value": item["risk_score"],
                    "status": item["risk_status"],
                }
                for item in risk_items
            ],
        },
        "role_scope": sorted(role.value for role in user.roles),
    }


@router.get("/accounts")
async def list_accounts(
    user: Annotated[CurrentUser, Depends(require_permission("read_customer"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        risk_items = await fetch_account_risk_items(connection)
    return {"items": risk_items}


@router.get("/account-risk")
async def account_risk(
    user: Annotated[CurrentUser, Depends(require_permission("read_customer"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        items = await fetch_account_risk_items(connection)
    return summarize_account_risk(items)


@router.get("/renewal-risk")
async def renewal_risk(
    user: Annotated[CurrentUser, Depends(require_permission("read_customer"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        items = await fetch_account_risk_items(connection)
    renewals: list[dict[str, Any]] = []
    for item in items:
        renewal = item.get("renewal_date")
        if not renewal:
            continue
        from datetime import UTC, date, datetime

        if isinstance(renewal, str):
            renewal_date = date.fromisoformat(renewal[:10])
        elif isinstance(renewal, datetime):
            renewal_date = renewal.date()
        else:
            renewal_date = renewal
        days_until = (renewal_date - datetime.now(UTC).date()).days
        if days_until < 0 or days_until > 120:
            continue
        renewals.append(
            {
                "external_id": item["external_id"],
                "name": item["name"],
                "renewal_date": item["renewal_date"],
                "days_until_renewal": days_until,
                "open_issues": item["open_issues"],
                "contract_value_gbp": item["contract_value_gbp"],
                "risk_status": item["risk_status"],
            }
        )
    renewals.sort(key=lambda row: row["days_until_renewal"])
    return {"items": renewals}


@router.get("/accounts/{external_id}")
async def account_360(
    external_id: str,
    user: Annotated[CurrentUser, Depends(require_permission("read_customer"))],
) -> dict[str, Any]:
    _ = user
    key = external_id.strip().upper()
    async with acquire() as connection:
        items = await fetch_account_risk_items(connection)
        account = next((item for item in items if item["external_id"] == key), None)
        if account is None:
            raise HTTPException(status_code=404, detail=f"Account {key} not found")
        issues = await connection.fetch(
            """
            SELECT i.issue_key, i.title, i.status::text, i.priority::text,
                   i.assigned_to, i.sla_due_at, i.updated_at
            FROM issues i
            JOIN customers c ON c.id = i.customer_id
            WHERE c.external_id = $1
              AND i.status IN ('open', 'in_progress')
            ORDER BY
              CASE i.priority
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END,
              i.updated_at DESC
            """,
            key,
        )
        actions = await connection.fetch(
            """
            SELECT na.action_text, na.owner, na.status::text, i.issue_key
            FROM next_actions na
            JOIN issues i ON i.id = na.issue_id
            JOIN customers c ON c.id = i.customer_id
            WHERE c.external_id = $1
              AND na.status IN ('pending', 'approved')
            ORDER BY na.created_at DESC
            LIMIT 10
            """,
            key,
        )
    return {
        "account": account,
        "open_issues": [dict(row) for row in issues],
        "next_actions": [dict(row) for row in actions],
    }


@router.get("/metrics/timeseries")
async def metrics_timeseries(
    user: Annotated[CurrentUser, Depends(require_permission("read_issues"))],
    metric: str = Query(default="open_issues"),
    days: int = Query(default=30, ge=7, le=90),
    customer_external_id: str | None = Query(default=None),
) -> dict[str, Any]:
    _ = user
    allowed = {
        "open_issues",
        "critical_issues",
        "sla_at_risk",
        "risk_score",
        "customers_at_risk",
    }
    if metric not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported metric: {metric}")

    async with acquire() as connection:
        if metric == "customers_at_risk":
            rows = await connection.fetch(
                """
                SELECT captured_at::date AS day, metric_value::float AS value
                FROM metric_snapshots
                WHERE metric_name = 'customers_at_risk'
                  AND labels->>'scope' = 'portfolio'
                  AND captured_at >= now() - ($1 || ' days')::interval
                ORDER BY day
                """,
                str(days),
            )
        elif customer_external_id:
            rows = await connection.fetch(
                """
                SELECT captured_at::date AS day, metric_value::float AS value
                FROM metric_snapshots
                WHERE metric_name = $1
                  AND labels->>'customer_external_id' = $2
                  AND captured_at >= now() - ($3 || ' days')::interval
                ORDER BY day
                """,
                metric,
                customer_external_id.strip().upper(),
                str(days),
            )
        else:
            rows = await connection.fetch(
                """
                SELECT captured_at::date AS day, sum(metric_value)::float AS value
                FROM metric_snapshots
                WHERE metric_name = $1
                  AND labels ? 'customer_external_id'
                  AND captured_at >= now() - ($2 || ' days')::interval
                GROUP BY captured_at::date
                ORDER BY day
                """,
                metric,
                str(days),
            )

    points = [
        {"date": row["day"].isoformat(), "value": float(row["value"])} for row in rows
    ]
    return {
        "metric": metric,
        "days": days,
        "customer_external_id": customer_external_id,
        "points": points,
    }


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
