# Relay — Acme Operations Command Desk

**Relay** is an agentic enterprise assistant for the fictional client **Acme Operations**. Staff ask operational questions; a LangGraph ReAct agent selects tools dynamically against PostgreSQL, Redis session memory, **MCP servers (wired into the agent)**, and **RBAC-aware RAG** (pgvector), with post-answer **groundedness** checks.

This tree is an original implementation (product **Relay** / **Command Desk**). It follows the same *architectural patterns* as the sibling inspiration project under the parent folder, but uses a distinct UI, seed data (Meridian / Cascade / Northline), and codebase — not a reskin.

> Located at `acme-relay/` inside the workspace. Prefer promoting this directory to its own git remote for submission.

## Quick start

```bash
cd acme-relay
cp .env.example .env   # add OPENAI_API_KEY for best LLM/embeddings quality
chmod +x infra/postgres/00-databases.sh
make demo              # docker compose up --build -d
make migrate-db        # if upgrading an existing Postgres volume
```

| Service | URL |
|---------|-----|
| Command Desk | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| MCP status | http://localhost:8000/api/mcp/status (auth) |
| Keycloak | http://localhost:8080 |
| Langfuse | http://localhost:3001 |
| GlitchTip | http://localhost:8001 |
| Grafana | http://localhost:3002 (admin / admin) |
| Prometheus | http://localhost:9090 |

### Demo users

| User | Password | Role |
|------|----------|------|
| `alice` | `alice123` | `sales_user` (read-only; no Postgres MCP) |
| `bob` | `bob123` | `support_user` (mutate via approval) |
| `dana` | `dana123` | `operations_user` (mutate + audit; no admin) |
| `admin` | `admin123` | `admin` |

Enable TOTP in Keycloak account console to demonstrate MFA.

### Seed accounts (cases)

- **Meridian Pay** (`MERIDIAN`) — CASE-2001 critical settlement
- **Cascade Retail Group** (`CASCADE`) — CASE-2002 webhooks
- **Northline Logistics** (`NORTHLINE`) — CASE-2003 POD delay

## Architecture

See [docs/architecture.md](docs/architecture.md), [docs/database-schema.md](docs/database-schema.md), [docs/threat-model.md](docs/threat-model.md), and [docs/tradeoffs.md](docs/tradeoffs.md).

```
Keycloak (MFA) → Relay Web (Command Desk)
                      ↓
                 FastAPI + LangGraph ReAct
                      ↓
     Native tools · Skills · MCP (domain/postgres/filesystem)
                      ↓
              Groundedness verifier
                      ↓
     PostgreSQL+pgvector (durable + RAG ACL) · Redis (session/Celery)
                      ↓
     Celery worker (ingest) · Langfuse · GlitchTip · Grafana
```

## Brief coverage

| Requirement | Relay |
|-------------|-------|
| Dynamic LLM tool use | LangGraph ReAct |
| Profile / open issues / summarise / next action | Native tools |
| MCP | Domain + Postgres + Filesystem **loaded into agent** |
| Groundedness | Post-answer verifier + `agent_runs` columns |
| Skill | Escalation (+ SLA, triage, handoff) |
| Keycloak + RBAC | sales / support / **operations** / admin + DB RBAC tables |
| Product UX | Dashboard, customers, issues, tasks, admin, account, trust/help |
| Postgres + Redis | pgvector Postgres + Redis Stack |
| Compose | `docker compose up` |
| K8s | Ingress + NetworkPolicy + MCP Deployments + Argo CD |
| Eval + observability | `evals/` + Langfuse/GlitchTip/Grafana |
| Docs | Architecture, schema, threat model, runbooks, CONTRIBUTING |

## MCP (agent integration)

Three MCP servers run in Compose/K8s. The chat agent loads their tools when `ENABLE_MCP_AGENT_TOOLS=true` (default):

| Server | Port | Example agent tool names |
|--------|------|--------------------------|
| Domain | 8090 | `domain_relay_get_customer_by_name`, `domain_relay_list_open_issues` |
| Filesystem | 8091 | `filesystem_fs_read_file`, `filesystem_fs_list_directory` |
| Postgres | 8092 | `postgres_postgres_query` (SELECT only; support/admin) |

- Status: `GET /api/mcp/status`
- Warm-up: API lifespan calls `warm_mcp_tools()` (non-fatal on failure)

## Knowledge ingest + RBAC RAG

```bash
# After login as bob/admin in UI: Knowledge → Run ingest
# Or enqueue via API POST /api/knowledge/ingest
```

Chunks store `allowed_roles` + `sensitivity`. `search_knowledge` filters by the caller’s JWT roles **before** vector ranking.

## Observability (Langfuse + more)

| System | What you see |
|--------|----------------|
| **Langfuse** http://localhost:3001 | Full agent run: LLM generations, tool spans, prompt name/version, session/user, request I/O |
| **Postgres audit** | Durable `tool_call_audit` (`source` native/mcp) + `agent_runs` (incl. groundedness) |
| **GlitchTip** | Exceptions / error tracking |
| **Grafana / Prometheus** | API metrics |

## Evaluation (live)

```bash
make demo
make eval-host   # or: make eval  (inside API container)
```

Scores tool selection, groundedness, RBAC, next-action/HITL, latency → [`evals/eval_results.md`](evals/eval_results.md).

## Quality

```bash
make quality                 # lint + pytest coverage ≥80%
make kustomize-build         # Ingress + NetworkPolicy present
```

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Kubernetes / Argo CD

See **[docs/argocd.md](docs/argocd.md)** and **[infra/kubernetes/README.md](infra/kubernetes/README.md)**.

- Kustomize base: api, worker, web, **MCP**, **Ingress**, **NetworkPolicies**, secrets example
- Argo CD Application: `infra/kubernetes/platform/argo-cd/applications.yaml`
- `make argocd-apply` after editing `repoURL` to your Git remote

## Submission deliverables

Assessment pack (mirrors Ops structure): **[deliverables/README.md](deliverables/README.md)**

| # | Artifact |
|---|----------|
| 1 | Repository access / zip |
| 2 | Setup, architecture, trade-offs |
| 3 | Architecture diagram (Mermaid) |
| 4 | Eval results + commentary |
| 5 | AI usage notes |
| 6 | Database design |
| 7 | Agentic AI & LangGraph |

```bash
make deliverables-zip   # → deliverables/relay-command-desk-source.zip
```

## AI usage notes

See [docs/ai-usage-notes.md](docs/ai-usage-notes.md) and [deliverables/05-ai-usage-notes.md](deliverables/05-ai-usage-notes.md).
