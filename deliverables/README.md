# Relay — Submission Deliverables

This folder contains the submission artifacts for the **Relay / Command Desk** assessment (Acme Operations fictional client).

| # | Deliverable | File |
|---|-------------|------|
| 1 | GitHub repository access or zip of code and configuration | [01-repository-access.md](./01-repository-access.md) |
| 2 | README — setup, architecture, trade-offs, AI tool usage | [02-setup-and-architecture.md](./02-setup-and-architecture.md) |
| 3 | Architecture diagram — system components and data flows | [03-architecture-diagram.mmd](./03-architecture-diagram.mmd) · [03-architecture-diagram.md](./03-architecture-diagram.md) |
| 4 | Eval results — evaluation set output with commentary | [04-eval-results.md](./04-eval-results.md) |
| 5 | AI usage notes — how AI tools were used during development | [05-ai-usage-notes.md](./05-ai-usage-notes.md) |
| 6 | Database design — PostgreSQL schema, ER diagrams, tables | [06-database-design.md](./06-database-design.md) |
| 7 | Agentic AI & LangGraph — graph topology, tools, routing | [07-agentic-ai-and-langgraph.md](./07-agentic-ai-and-langgraph.md) |

## Package source zip

```bash
make deliverables-zip
# → deliverables/relay-command-desk-source.zip
```

## Quick links (running system)

| Service | URL |
|---------|-----|
| Command Desk | http://localhost:5173 |
| Dashboard | http://localhost:5173/dashboard |
| API (OpenAPI) | http://localhost:8000/docs |
| MCP status | http://localhost:8000/api/mcp/status (auth) |
| Keycloak | http://localhost:8080 |
| Langfuse | http://localhost:3001 |
| GlitchTip | http://localhost:8001 |
| Grafana | http://localhost:3002 |
| Prometheus | http://localhost:9090 |

### Demo users

| User | Password | Role |
|------|----------|------|
| `alice` | `alice123` | `sales_user` |
| `bob` | `bob123` | `support_user` |
| `dana` | `dana123` | `operations_user` |
| `admin` | `admin123` | `admin` |

## Related documentation (in-repo)

- Root README: [`../README.md`](../README.md)
- Architecture: [`../docs/architecture.md`](../docs/architecture.md)
- Trade-offs: [`../docs/tradeoffs.md`](../docs/tradeoffs.md)
- Threat model: [`../docs/threat-model.md`](../docs/threat-model.md)
- Database schema: [`../docs/database-schema.md`](../docs/database-schema.md)
- Kubernetes: [`../infra/kubernetes/README.md`](../infra/kubernetes/README.md)
- Contributing / CI: [`../docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md)
