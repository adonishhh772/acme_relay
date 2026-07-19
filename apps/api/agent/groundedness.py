"""Post-answer groundedness verification against tool evidence."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field


class GroundednessResult(BaseModel):
    passed: bool
    unsupported_claims: list[str] = Field(default_factory=list)
    evidence_ids_used: list[str] = Field(default_factory=list)
    explanation: str


_CASE_RE = re.compile(r"\bCASE[-\s]?\d+\b", re.I)
_ACCOUNT_RE = re.compile(r"\b(MERIDIAN|CASCADE|NORTHLINE)\b", re.I)
_STATUS_WORDS = (
    "open",
    "in_progress",
    "resolved",
    "critical",
    "high priority",
    "sla",
)


def _collect_evidence_ids(tool_calls: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for tool_call in tool_calls:
        result = tool_call.get("result")
        if not isinstance(result, dict):
            continue
        for evidence in result.get("evidence", []):
            if isinstance(evidence, dict) and evidence.get("id"):
                ids.append(str(evidence["id"]))
        customer = result.get("customer")
        if isinstance(customer, dict) and customer.get("external_id"):
            ids.append(str(customer["external_id"]))
        for issue in result.get("open_issues", []) or []:
            if isinstance(issue, dict) and issue.get("issue_key"):
                ids.append(str(issue["issue_key"]))
    return ids


def _tool_corpus(tool_calls: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for tool_call in tool_calls:
        result = tool_call.get("result")
        if result is not None:
            parts.append(json.dumps(result, default=str).lower())
    return " ".join(parts)


def _answer_looks_factual(answer: str) -> bool:
    lower = answer.lower()
    if _CASE_RE.search(answer) or _ACCOUNT_RE.search(answer):
        return True
    if any(word in lower for word in _STATUS_WORDS):
        return True
    if re.search(r"\b(issue|case)\b", lower) and re.search(
        r"\b(customer|account)\b", lower
    ):
        return True
    return False


def verify_groundedness(
    answer: str,
    tool_calls: list[dict[str, Any]],
) -> GroundednessResult:
    evidence_ids = _collect_evidence_ids(tool_calls)
    corpus = _tool_corpus(tool_calls)

    safe_phrases = (
        "permission denied",
        "approval",
        "approved action",
        "cannot verify",
        "missing information",
        "not found",
        "partial information",
        "how can i help",
        "you're welcome",
        "goodbye",
        "what would you like",
        "pending approval",
        "requires approval",
    )
    lower_answer = answer.lower()
    if any(phrase in lower_answer for phrase in safe_phrases):
        return GroundednessResult(
            passed=True,
            evidence_ids_used=evidence_ids,
            explanation="Response is operational (permission, approval, or explicit uncertainty).",
        )

    if not tool_calls:
        if _answer_looks_factual(answer):
            return GroundednessResult(
                passed=False,
                unsupported_claims=["Factual claims without tool-backed evidence"],
                explanation=(
                    "No tools were invoked but the answer appears to assert "
                    "customer/case facts."
                ),
            )
        return GroundednessResult(
            passed=True,
            explanation="Non-factual or general guidance without database claims.",
        )

    unsupported: list[str] = []
    corpus_compact = corpus.replace(" ", "").replace("-", "").lower()
    for match in _CASE_RE.findall(answer):
        token = re.sub(r"\s+", "-", match.upper())
        token_compact = token.replace("-", "").lower()
        if token_compact not in corpus_compact:
            unsupported.append(f"Case reference '{match}' not found in tool outputs")

    for match in _ACCOUNT_RE.findall(answer):
        if match.lower() not in corpus:
            unsupported.append(f"Account reference '{match}' not found in tool outputs")

    if unsupported:
        cautious = (
            "I found partial information from Relay data, but I cannot fully verify every "
            "claim in the draft answer. Unsupported items: "
            + "; ".join(unsupported[:3])
        )
        return GroundednessResult(
            passed=False,
            unsupported_claims=unsupported,
            evidence_ids_used=evidence_ids,
            explanation=cautious,
        )

    return GroundednessResult(
        passed=True,
        evidence_ids_used=evidence_ids,
        explanation=(
            f"Answer aligned with {len(tool_calls)} tool invocation(s) "
            f"and {len(evidence_ids)} evidence record(s)."
        ),
    )


def apply_groundedness_policy(answer: str, verification: GroundednessResult) -> str:
    """Return the answer unchanged; groundedness details are returned separately."""
    _ = verification
    return answer
