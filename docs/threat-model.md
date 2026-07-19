# Threat model (Relay)

## Assets

- Customer and case data in PostgreSQL
- JWT access tokens (Keycloak)
- LLM / embedding API keys
- Audit logs (`agent_runs`, `tool_call_audit`)
- Knowledge corpus with role ACLs

## Trust boundaries

| Boundary | Control |
|----------|---------|
| Browser → API | Keycloak JWT; Ingress TLS in Kubernetes |
| API → PostgreSQL | ClusterIP / NetworkPolicy; app-level RBAC |
| API → LLM | Server-side keys only |
| API → MCP | SSE inside Docker/K8s network; NetworkPolicy API→MCP only |
| MCP postgres → DB | SELECT-only keyword blocklist |
| RAG → caller | `allowed_roles` filter before vector distance |

## Key risks

1. **Over-privileged token** — Mitigated by `auth/rbac.py` per-tool and MCP-prefix permissions.
2. **Hallucinated answers** — Mitigated by tool-first agent + `verify_groundedness`.
3. **Unauthorized writes** — HITL for mutating tools; sales cannot mutate.
4. **SQL abuse via MCP** — Postgres MCP rejects non-SELECT / dangerous keywords.
5. **Knowledge leakage** — Chunk ACL intersection with JWT roles before ranking.
6. **Lateral movement in cluster** — Default-deny NetworkPolicy + allowlists.

## Out of scope (current demo)

- mTLS between services
- Postgres row-level security
- PII redaction in Langfuse traces
- External Secrets Operator wiring
