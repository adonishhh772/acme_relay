# Relay — Acme Operations Command Desk

**Relay** is an agentic enterprise assistant for the fictional client **Acme Operations**. Staff ask operational questions; a LangGraph ReAct agent selects tools dynamically against PostgreSQL, Redis session memory, **MCP servers (wired into the agent)**, and **RBAC-aware RAG** (pgvector), with post-answer **groundedness** checks.

This tree is an original implementation (product **Relay** / **Command Desk**). It follows the same *architectural patterns* as the sibling inspiration project under the parent folder, but uses a distinct UI, seed data (VaultLedger / Nexus Freight / Aurora Bank), and codebase — not a reskin.

> Located at `acme-relay/` inside the workspace. Prefer promoting this directory to its own git remote for submission.

## Quick start

```bash
cd acme-relay
cp .env.example .env   # add OPENAI_API_KEY for best LLM/embeddings quality
chmod +x infra/postgres/00-databases.sh
make demo              # docker compose up --build -d
make migrate-db        # if upgrading an existing Postgres volume
```

| Service | URL (HTTP) | URL (HTTPS — `make tls-up`) |
|---------|------------|-------------------------------|
| Command Desk | http://localhost:5173 | https://acme-relay.local |
| API docs | http://localhost:8000/docs | https://api.acme-relay.local/docs |
| MCP status | http://localhost:8000/api/mcp/status (auth) | https://api.acme-relay.local/api/mcp/status |
| Keycloak | http://localhost:8080 | https://auth.acme-relay.local |
| Langfuse | http://localhost:3001 | https://langfuse.local |
| GlitchTip | http://localhost:8001 | https://glitchtip.local |
| Grafana | http://localhost:3002 (admin / admin) | https://grafana.local |

### Local HTTPS (mkcert + Caddy)

```bash
brew install mkcert nss   # once
make tls-certs            # trust local CA + write certs + /etc/hosts
make tls-up               # stack behind https://*.local
```

See [docs/local-https.md](docs/local-https.md). Plain `make demo` still uses localhost HTTP.

### Demo users

| User | Password | Role |
|------|----------|------|
| `alice` | `alice123` | `sales_user` (read-only; no Postgres MCP) |
| `bob` | `bob123` | `support_user` (mutate via approval) |
| `dana` | `dana123` | `operations_user` (mutate + audit; no admin) |
| `admin` | `admin123` | `admin` |

Enable TOTP in Keycloak account console to demonstrate MFA.

### Seed accounts (cases)

- **VaultLedger Payments** (`VAULTLEDGER`) — OPS-3101 critical settlement · £680k · renewal 2026-09-30
- **Aurora Bank** (`AURORABANK`) — OPS-3102 payment webhooks · £185k · renewal 2026-08-20
- **Nexus Freight** (`NEXUSFREIGHT`) — OPS-3103 POD delay · £420k · renewal 2026-11-15

### Account management (Command Desk)

- Customer commercial fields: contract value, renewal date, account/support managers
- Account risk scores + Account 360 drawer on `/customers`
- Dashboard AM KPIs, renewal panel, bar charts + 30-day line trends (`metric_snapshots`)
- Assistant profile tool returns AM fields for VaultLedger / Nexus / Aurora

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

Rich demo corpus under `infra/knowledge/` (mounted at `/data/knowledge`):

| Tier | Docs | Roles |
|------|------|-------|
| **Public** | Command Desk business value; tier/SLA/commercial guide | all staff |
| **Internal** | Escalation; VaultLedger / Aurora / Nexus runbooks; HITL approvals | support, operations, admin |
| **Restricted** | Executive incident protocol; commercial renewal war-room | admin only |

```bash
make migrate-db   # refresh knowledge_documents catalog (07-knowledge-business-value.sql)
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
| **Grafana** | API metrics dashboards |

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
