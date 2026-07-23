from agent.groundedness import (
    GroundednessResult,
    apply_groundedness_policy,
    verify_groundedness,
)


def test_apply_groundedness_policy_returns_answer_unchanged_when_failed() -> None:
    answer = "OPS-9999 is critical for VaultLedger."
    verification = GroundednessResult(
        passed=False,
        unsupported_claims=["Case reference 'OPS-9999' not found in tool outputs"],
        explanation="Partial information.",
    )
    assert apply_groundedness_policy(answer, verification) == answer


def test_safe_phrases_pass_without_tools() -> None:
    result = verify_groundedness("Permission denied for this role.", [])
    assert result.passed is True


def test_factual_without_tools_fails() -> None:
    result = verify_groundedness(
        "OPS-3101 is critical for VaultLedger Payments and SLA is breached.",
        [],
    )
    assert result.passed is False
    assert result.unsupported_claims


def test_general_guidance_without_tools_passes() -> None:
    result = verify_groundedness("How can I help you today?", [])
    assert result.passed is True


def test_case_reference_must_appear_in_tool_corpus() -> None:
    tool_calls = [
        {
            "tool": "get_open_issues",
            "result": {
                "ok": True,
                "open_issues": [{"issue_key": "OPS-3101", "priority": "critical"}],
            },
        }
    ]
    ok = verify_groundedness("OPS-3101 is critical.", tool_calls)
    assert ok.passed is True

    bad = verify_groundedness("OPS-9999 is critical.", tool_calls)
    assert bad.passed is False


def test_account_reference_must_appear_in_tool_corpus() -> None:
    tool_calls = [
        {
            "tool": "get_customer_profile_by_name",
            "result": {
                "ok": True,
                "customer": {"external_id": "VAULTLEDGER", "name": "VaultLedger Payments"},
            },
        }
    ]
    ok = verify_groundedness("VAULTLEDGER is an enterprise account.", tool_calls)
    assert ok.passed is True

    bad = verify_groundedness("AURORABANK is an enterprise account.", tool_calls)
    assert bad.passed is False
