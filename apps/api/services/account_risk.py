"""Account risk scoring for Relay desk / AM views."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Literal

RiskStatus = Literal["green", "amber", "red"]

TIER_WEIGHTS = {"strategic": 20, "enterprise": 10, "standard": 0}


def renewal_within_days(renewal_date: date | datetime | str | None, days: int) -> bool:
    if not renewal_date:
        return False
    if isinstance(renewal_date, datetime):
        renewal = renewal_date.date()
    elif isinstance(renewal_date, date):
        renewal = renewal_date
    else:
        try:
            renewal = datetime.fromisoformat(str(renewal_date).replace("Z", "+00:00")).date()
        except ValueError:
            return False
    delta = (renewal - datetime.now(UTC).date()).days
    return 0 <= delta <= days


def compute_risk_score(
    *,
    critical_issues: int,
    high_issues: int,
    medium_issues: int,
    sla_at_risk: int,
    pending_next_actions: int,
    tier: str,
    renewal_date: date | datetime | str | None,
    has_high_or_critical_open: bool,
) -> int:
    score = 0
    score += critical_issues * 30
    score += high_issues * 20
    score += medium_issues * 10
    score += sla_at_risk * 25
    score += pending_next_actions * 8
    score += TIER_WEIGHTS.get((tier or "standard").lower(), 0)
    if renewal_within_days(renewal_date, 60) and has_high_or_critical_open:
        score += 20
    return score


def risk_status_from_score(score: int) -> RiskStatus:
    if score >= 70:
        return "red"
    if score >= 40:
        return "amber"
    return "green"


def recommended_action(risk_status: RiskStatus, *, critical_issues: int, sla_at_risk: int, renewal_date: Any) -> str:
    if risk_status == "red":
        if critical_issues > 0:
            return "Escalate critical issues and coordinate with Support before customer outreach."
        return "Schedule urgent account review with Support and account leadership."
    if risk_status == "amber":
        if sla_at_risk > 0:
            return "Check SLA status with Support and prepare a customer-safe update."
        return "Review open issues and confirm follow-up owners."
    if renewal_within_days(renewal_date, 90):
        return "Confirm renewal timeline and address any open concerns proactively."
    return "Monitor account health; no immediate action required."


def build_account_risk_row(row: dict[str, Any]) -> dict[str, Any]:
    critical = int(row.get("critical_issues") or 0)
    high = int(row.get("high_issues") or 0)
    medium = int(row.get("medium_issues") or 0)
    sla_at_risk = int(row.get("sla_at_risk") or 0)
    pending = int(row.get("pending_next_actions") or 0)
    tier = str(row.get("tier") or "standard")
    renewal = row.get("renewal_date")
    score = compute_risk_score(
        critical_issues=critical,
        high_issues=high,
        medium_issues=medium,
        sla_at_risk=sla_at_risk,
        pending_next_actions=pending,
        tier=tier,
        renewal_date=renewal,
        has_high_or_critical_open=(critical + high) > 0,
    )
    status = risk_status_from_score(score)
    contract = row.get("contract_value_gbp")
    return {
        "external_id": row["external_id"],
        "name": row["name"],
        "industry": row.get("industry"),
        "tier": tier,
        "region": row.get("region"),
        "account_owner": row.get("account_owner"),
        "support_manager": row.get("support_manager"),
        "account_manager": row.get("account_manager"),
        "contract_value_gbp": float(contract) if contract is not None else None,
        "renewal_date": renewal.isoformat() if hasattr(renewal, "isoformat") else renewal,
        "open_issues": int(row.get("open_issues") or 0),
        "critical_issues": critical,
        "high_issues": high,
        "medium_issues": medium,
        "sla_at_risk": sla_at_risk,
        "pending_next_actions": pending,
        "risk_score": score,
        "risk_status": status,
        "recommended_action": recommended_action(
            status,
            critical_issues=critical,
            sla_at_risk=sla_at_risk,
            renewal_date=renewal,
        ),
    }
