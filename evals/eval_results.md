# Relay Evaluation Results

**Generated:** 2026-07-22T21:02:27.519950+00:00
**API:** http://127.0.0.1:8000
**Mode:** live Keycloak + /api/chat
**Pass rate:** 7/10 (70%)

## Summary

| Metric | Value |
|--------|-------|
| Total | 10 |
| Passed | 7 |
| Failed | 3 |
| Tool selection pass | 7 |
| Groundedness pass | 7 |
| RBAC pass | 7 |
| Next-action pass | 7 |
| Avg latency (ms) | 10625 |

## Per-question results

| ID | Role | Tools | Grounded | RBAC | Next action | Latency | Status |
|----|------|-------|----------|------|-------------|---------|--------|
| eval_01 | sales_user | domain_relay_list_open_issues, get_customer_profile_by_name, get_open_issues | ✓ | ✓ | ✓ | 15554 | PASS |
| eval_02 | sales_user | — | ✓ | ✓ | ✓ | 2058 | PASS |
| eval_03 | support_user | domain_relay_list_open_issues, get_customer_profile_by_name, get_open_issues | ✓ | ✓ | ✓ | 8167 | PASS |
| eval_04 | support_user | summarize_issue_history | ✓ | ✓ | ✓ | 3887 | PASS |
| eval_05 | support_user | get_customer_profile_by_name, run_escalation_summary_skill | ✓ | ✓ | ✓ | 6266 | PASS |
| eval_06 | sales_user | search_knowledge | ✓ | ✓ | ✓ | 3677 | PASS |
| eval_07 | admin | search_knowledge | ✓ | ✓ | ✓ | 66641 | PASS |
| eval_08 | support_user | — | — | — | — | 0 | FAIL |
| eval_09 | sales_user | — | — | — | — | 0 | FAIL |
| eval_10 | support_user | — | — | — | — | 0 | FAIL |

## Commentary

- Tool selection: agent must call DB/RAG tools — not invent VaultLedger/Nexus Freight facts.
- Groundedness: answers cite OPS-* keys and seeded account owners, or clear RBAC denial.
- RBAC: sales cannot create next actions; restricted knowledge hidden from sales.
- Next actions: support stages HITL approvals; admin approves in Command Desk.
- Traces: inspect Langfuse (http://localhost:3001) for LLM + tool spans per request_id.

### eval_08
- Error: HTTP 500: Internal Server Error
- Answer preview: 

### eval_09
- Error: Server disconnected without sending a response.
- Answer preview: 

### eval_10
- Error: HTTP 500: Internal Server Error
- Answer preview: 

