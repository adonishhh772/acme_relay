# Relay architecture

## Components

- **Web (Command Desk):** React + Vite + Keycloak-js — Assistant, Desk, Accounts, Cases, Approvals, Knowledge, Audit, Governance.
- **API:** FastAPI — JWT validation, RBAC, chat agent, desk APIs, approvals, knowledge enqueue, audit, governance, MCP status.
- **Agent:** Single LangGraph `create_react_agent` with **native tools + skills + MCP tools** (SSE via `langchain-mcp-adapters`). Redis checkpointer for thread memory.
- **Groundedness:** Post-answer verifier compares claims (case keys, account ids) against the tool-call corpus; result stored on `agent_runs` and returned on `ChatResponse`.
- **Worker:** Celery consumer — chunk/embed knowledge into pgvector with ACL metadata.
- **MCP:** Domain (customer/cases), Postgres (SELECT-only), Filesystem (knowledge files). Loaded into the agent when `ENABLE_MCP_AGENT_TOOLS=true`.
- **Data:** PostgreSQL 16 + pgvector (system of record + RAG); Redis (sessions, Celery broker, checkpoints).
- **Auth:** Keycloak realm `acme` with TOTP policy and roles `sales_user`, `support_user`, `operations_user`, `admin` (+ DB RBAC tables).
- **Obs:** Langfuse (LLM + tool spans + run I/O + prompt versions), Postgres audit mirror, GlitchTip (errors), Prometheus/Grafana (metrics).
- **GitOps:** Kubernetes Deployments + Ingress + NetworkPolicies + Argo CD Application CR (see [argocd.md](argocd.md)).

## Request path

1. User authenticates (Keycloak, optional TOTP).
2. Chat request carries bearer token → API maps realm roles → `ToolContext`.
3. ReAct agent selects tools (native, skills, MCP); mutating tools stage HITL approvals.
4. Tool audit rows written with `source` = `native` | `mcp`; session turns stored in Redis.
5. `verify_groundedness` runs against `tool_calls_log`; answer + groundedness payload returned.
6. RAG queries apply `allowed_roles && user_roles` then order by embedding distance.

## MCP integration

```text
API startup → warm_mcp_tools()
                ↓
MultiServerMCPClient (SSE)
  domain      → http://mcp-domain:8090/sse
  filesystem  → http://mcp-filesystem:8091/sse
  postgres    → http://mcp-postgres:8092/sse
                ↓
wrap_mcp_tools_for_context → ToolContext.run_mcp (RBAC + audit)
                ↓
create_react_agent tool list
```

Status probe: `GET /api/mcp/status` (auth required).

RBAC for MCP prefixes:

| Prefix | Permission | Roles |
|--------|------------|-------|
| `domain_*` | `mcp_read` | sales, support, admin |
| `filesystem_*` | `mcp_read` | sales, support, admin |
| `postgres_*` | `mcp_sql` | support, admin |

## Scaling seams

- Stateless API replicas behind Ingress.
- Independent Celery worker replicas for ingest.
- MCP servers scale independently; NetworkPolicy allows only API → MCP.
- Postgres connection pooling / read replicas for dashboards and RAG reads.
- Redis for ephemeral fan-out; never the sole durable store for cases.

## Related docs

- [database-schema.md](database-schema.md)
- [threat-model.md](threat-model.md)
- [production-readiness.md](production-readiness.md)
- [skills.md](skills.md)
- [tradeoffs.md](tradeoffs.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
