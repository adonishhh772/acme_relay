"""Desk / account-management query helpers."""

from __future__ import annotations

from typing import Any

from services.account_risk import build_account_risk_row, renewal_within_days


ACCOUNT_RISK_SQL = """
SELECT
    c.id AS customer_id,
    c.external_id,
    c.name,
    c.industry,
    c.tier,
    c.region,
    c.account_owner,
    c.support_manager,
    c.account_manager,
    c.contract_value_gbp,
    c.renewal_date,
    COUNT(i.id) FILTER (WHERE i.status IN ('open', 'in_progress')) AS open_issues,
    COUNT(i.id) FILTER (
        WHERE i.status IN ('open', 'in_progress') AND i.priority = 'critical'
    ) AS critical_issues,
    COUNT(i.id) FILTER (
        WHERE i.status IN ('open', 'in_progress') AND i.priority = 'high'
    ) AS high_issues,
    COUNT(i.id) FILTER (
        WHERE i.status IN ('open', 'in_progress') AND i.priority = 'medium'
    ) AS medium_issues,
    COUNT(i.id) FILTER (
        WHERE i.status IN ('open', 'in_progress')
          AND i.sla_due_at IS NOT NULL
          AND i.sla_due_at <= now() + interval '24 hours'
    ) AS sla_at_risk,
    (
        SELECT COUNT(*)
        FROM next_actions na
        JOIN issues ix ON ix.id = na.issue_id
        WHERE ix.customer_id = c.id AND na.status = 'pending'
    ) AS pending_next_actions
FROM customers c
LEFT JOIN issues i ON i.customer_id = c.id
WHERE c.is_active = true
GROUP BY c.id
ORDER BY c.name
"""


async def fetch_account_risk_items(connection: Any) -> list[dict[str, Any]]:
    rows = await connection.fetch(ACCOUNT_RISK_SQL)
    items = [build_account_risk_row(dict(row)) for row in rows]
    items.sort(key=lambda item: item["risk_score"], reverse=True)
    return items


def summarize_account_risk(items: list[dict[str, Any]]) -> dict[str, Any]:
    at_risk = [item for item in items if item["risk_score"] >= 40]
    high_risk = [item for item in items if item["risk_score"] >= 70]
    contract_at_risk = sum(
        item["contract_value_gbp"] or 0 for item in at_risk if item.get("contract_value_gbp")
    )
    renewals_at_risk = sum(
        1
        for item in items
        if item.get("renewal_date")
        and renewal_within_days(item["renewal_date"], 60)
        and item["open_issues"] > 0
    )
    return {
        "customers": items,
        "total_at_risk": len(at_risk),
        "total_high_risk": len(high_risk),
        "contract_value_at_risk_gbp": contract_at_risk,
        "renewals_at_risk": renewals_at_risk,
    }
