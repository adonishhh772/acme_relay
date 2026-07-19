# Relay database schema

PostgreSQL 16 + `pgvector`. Applied via `infra/postgres/init.sql` (fresh volume), then idempotent:

- `03-schema-enrichment.sql`
- `04-rbac-operations-parity.sql` (`make migrate-db`)

## Domain tables

| Table | Purpose |
|-------|---------|
| `organizations` | Tenant (`acme-ops`) |
| `customers` | Accounts (+ `organization_id`) |
| `users` / `user_roles` | Local role mirror (+ `organization_id`) |
| `issues` / `issue_updates` | Cases / timeline |
| `next_actions` | Approved follow-ups |
| `user_tasks` | Personal My Tasks queue |

## RBAC (Ops-aligned)

| Table | Purpose |
|-------|---------|
| `permissions` | Permission keys (`read_customer`, `manage_users`, …) |
| `rbac_roles` | System roles incl. `operations_user` |
| `role_permissions` | Role → permission grants |
| `user_role_assignments` | Optional DB role overlay per org |

Roles (`app_role`): `sales_user`, `support_user`, `operations_user`, `admin`.

## Agent / audit

| Table | Purpose |
|-------|---------|
| `tool_call_audit` | Tool calls; `source` = `native` \| `mcp` |
| `agent_runs` | Chat runs + groundedness columns |
| `pending_approvals` | Durable HITL staging |
| `prompt_versions` | Prompt registry |
| `eval_runs` | Eval suite results |
| `metric_snapshots` | KPI samples |
| `schema_migrations` | Applied versions |

## Knowledge / feedback

| Table | Purpose |
|-------|---------|
| `knowledge_documents` / `knowledge_chunks` | ACL RAG (pgvector) + org metadata |
| `issue_csat_responses` | CSAT scores |
| `chat_feedback_events` | Thumbs up/down on chat |

## RAG filter

```sql
WHERE c.allowed_roles && $2::app_role[]
ORDER BY c.embedding <=> $1::vector
```
