# Relay skills

Skills are reusable, structured workflows exposed as LangGraph tools. They compose native DB reads and return structured JSON for the ReAct agent.

| Skill tool name | Purpose |
|-----------------|---------|
| `run_escalation_summary_skill` | Compact escalation brief for a customer |
| `run_sla_breach_assessment_skill` | SLA risk / breach assessment |
| `run_issue_triage_skill` | Prioritised triage suggestions |
| `run_shift_handoff_skill` | Shift handoff narrative |

Implementation: `apps/api/skills/` + `skills/registry.py`.

All skills require `run_skill` permission (sales, support, admin).
