"""Unit tests for account risk scoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from services.account_risk import (
    build_account_risk_row,
    compute_risk_score,
    risk_status_from_score,
)


def test_risk_status_thresholds() -> None:
    assert risk_status_from_score(30) == "green"
    assert risk_status_from_score(50) == "amber"
    assert risk_status_from_score(80) == "red"


def test_compute_risk_score_critical_and_renewal() -> None:
    renewal = datetime.now(UTC).date() + timedelta(days=30)
    score = compute_risk_score(
        critical_issues=1,
        high_issues=0,
        medium_issues=0,
        sla_at_risk=1,
        pending_next_actions=1,
        tier="strategic",
        renewal_date=renewal,
        has_high_or_critical_open=True,
    )
    assert score >= 70
    assert risk_status_from_score(score) == "red"


def test_build_account_risk_row() -> None:
    row = build_account_risk_row(
        {
            "external_id": "VAULTLEDGER",
            "name": "VaultLedger Payments",
            "tier": "strategic",
            "critical_issues": 1,
            "high_issues": 0,
            "medium_issues": 1,
            "sla_at_risk": 1,
            "pending_next_actions": 1,
            "open_issues": 2,
            "contract_value_gbp": 680000,
            "renewal_date": datetime.now(UTC).date() + timedelta(days=40),
        }
    )
    assert row["external_id"] == "VAULTLEDGER"
    assert row["risk_score"] > 0
    assert row["risk_status"] in ("green", "amber", "red")
    assert "recommended_action" in row
