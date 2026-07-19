# Relay Evaluation Results

**Generated:** 2026-07-18T23:00:53.659797+00:00
**API:** http://127.0.0.1:8000

Run against a live stack with role tokens for full scoring.
This checked-in summary documents the suite design and expected behaviours.

| ID | Role | Expected tools | RBAC note |
|----|------|----------------|-----------|
| eval_01 | sales_user | get_open_issues, run_escalation_summary_skill, summarize_issue_history | Primary demo flow |
| eval_02 | sales_user | create_next_action | Sales must not create next actions |
| eval_03 | support_user | get_open_issues | allow |
| eval_04 | support_user | summarize_issue_history | allow |
| eval_05 | support_user | run_escalation_summary_skill | allow |
| eval_06 | sales_user | search_knowledge | RBAC RAG — sales must not receive restricted admin doc content |
| eval_07 | admin | search_knowledge | allow |
| eval_08 | support_user | run_sla_breach_assessment_skill, get_open_issues | allow |
| eval_09 | sales_user | get_customer_profile_by_name | allow |
| eval_10 | support_user | create_next_action | Should stage HITL approval |

## Commentary

- Tool selection: agent must call DB/RAG tools — not invent Meridian/Cascade facts.
- Groundedness: answers cite CASE-* keys and seeded account owners.
- RBAC: sales cannot create next actions; restricted knowledge hidden from sales.
- Next actions: support stages HITL approvals; admin approves in Command Desk.

