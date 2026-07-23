# Deliverable 2 — Setup, Architecture & Trade-offs

## Relay — Acme Operations Command Desk

Enterprise agentic assistant for fictional **Acme Operations**. Staff ask operational questions; a LangGraph ReAct agent selects tools dynamically against PostgreSQL + pgvector (ACL RAG), Redis, Keycloak RBAC (incl. `operations_user`), MCP servers wired into the agent, Celery ingest, and groundedness verification.

---

## Setup instructions

### Prerequisites

| Tool | Version |
|------|---------|
| Docker & Docker Compose | 24+ |
| Python | 3.11+ (local tests / evals) |
| Node.js | 20+ (web / Playwright) |
| Make | GNU Make |

Optional: `kubectl` for Kubernetes / Argo CD chapter.

### Quick start (recommended)

```bash
cp .env.example .env          # add OPENAI_API_KEY
chmod +x infra/postgres/00-databases.sh
brew install mkcert nss       # once — local HTTPS
make demo                     # TLS stack (Caddy + *.local)
make migrate-db               # RBAC + tasks + CSAT enrichment
```

Prerequisite: **mkcert** (for `make demo` HTTPS). HTTP-only: `make demo-http`.

| Service | URL |
|---------|-----|
| **Command Desk** | https://acme-relay.local |
| **Dashboard** | https://acme-relay.local/dashboard |
| **API docs** | https://api.acme-relay.local/docs |
| **Keycloak** | https://auth.acme-relay.local |
| **Langfuse** | https://langfuse.local |
| **GlitchTip** | https://glitchtip.local |
| **Grafana** | https://grafana.local |

### Environment configuration

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Chat + embeddings (`text-embedding-3-small`) |
| `ENABLE_MCP_AGENT_TOOLS` | Load MCP tools into ReAct agent (default `true`) |
| `MCP_DOMAIN_URL` / `MCP_FILESYSTEM_URL` / `MCP_POSTGRES_URL` | SSE MCP bases |
| `ENABLE_LANGFUSE` / `ENABLE_GLITCHTIP` | Observability toggles |
| `KEYCLOAK_URL`, `KEYCLOAK_ISSUER`, `KEYCLOAK_REALM` | Auth (must match eval runner) |

### Common commands

```bash
make up                 # docker compose up --build
make demo               # start stack
make migrate-db         # 03 + 04 SQL enrichment
make reseed-db          # reload seed cases
make eval / eval-host   # 10-question suite
make test               # API pytest + Vitest
make test-coverage      # ≥80% API coverage
make security-audit     # bandit + pip-audit + npm audit
make test-e2e           # Playwright + docker-compose.e2e.yml
make kustomize-build    # Ingress + NetworkPolicy present
make deliverables-zip   # source zip for this pack
```

### Demo accounts

| User | Password | Role |
|------|----------|------|
| `alice` | `alice123` | `sales_user` (read-only) |
| `bob` | `bob123` | `support_user` (mutate via HITL) |
| `dana` | `dana123` | `operations_user` (mutate + audit) |
| `admin` | `admin123` | `admin` |

Seed accounts: **VaultLedger Payments** (`VAULTLEDGER` / OPS-3101), **Nexus Freight** (`NEXUSFREIGHT` / OPS-3102), **Aurora Bank** (`AURORABANK` / OPS-3103).

---

## Architecture overview

### System-level view

```text
React Command Desk (Keycloak SSO + TOTP)
    │ Bearer JWT
    ▼
FastAPI API
    ├── /api/chat            — LangGraph ReAct + groundedness
    ├── /api/desk            — Dashboard KPIs, customers, issues
    ├── /api/tasks           — My Tasks queue
    ├── /api/approvals       — HITL stage/decide
    ├── /api/knowledge       — Docs + Celery ingest enqueue
    ├── /api/admin           — Users / roles / orgs
    ├── /api/account         — Profile + security links
    ├── /api/evaluations     — Eval run browser
    ├── /api/governance      — Active prompt version
    └── /api/mcp/status      — MCP reachability + agent tool load
    ▼
LangGraph ReAct agent
    ├── Native tools         — RBAC, HITL, audit
    ├── Skills (4)           — Escalation, SLA, triage, handoff
    ├── MCP tools (SSE)      — domain · filesystem · postgres
    └── Groundedness verifier
    ▼
Data & infra
    ├── PostgreSQL 16 + pgvector — OLTP + ACL RAG chunks
    ├── Redis Stack              — sessions, checkpoints, Celery broker
    ├── Celery worker            — chunk/embed knowledge
    └── Keycloak                 — identity + 4 realm roles
```

### Request lifecycle (chat)

1. User signs in via Keycloak; frontend holds JWT.
2. `POST /api/chat` validates token → `ToolContext` with roles.
3. `invoke_agent` builds ReAct graph with native + skill + MCP tools.
4. Tool calls audited (`source` = `native` \| `mcp`); mutations stage HITL.
5. `verify_groundedness` checks case/account claims against tool corpus.
6. Persist `agent_runs` (incl. groundedness) + return `ChatResponse`.

### Identity & RBAC

```text
Keycloak realm roles
  → apps/api/auth/rbac.py PERMISSIONS
  → tool_allowed / MCP prefix permissions
  → knowledge_chunks.allowed_roles && user_roles (SQL before vector rank)

DB overlay (parity):
  organizations → permissions / rbac_roles / role_permissions / user_role_assignments
```

### MCP servers

| Server | Port | Agent tool prefix examples |
|--------|------|----------------------------|
| domain | 8090 | `domain_relay_get_customer_by_name` |
| filesystem | 8091 | `filesystem_fs_read_file` |
| postgres | 8092 | `postgres_postgres_query` (support/ops/admin) |

Loaded at API startup via `warm_mcp_tools()` when `ENABLE_MCP_AGENT_TOOLS=true`.

### RAG knowledge pipeline

```text
infra/knowledge/{public,internal,restricted}/*.md
  → Celery ingest (chunk + embed)
  → knowledge_chunks.embedding (pgvector) + allowed_roles
  → search_knowledge (filter roles, then <=> distance)
  → groundedness verifier
```

### Observability

| System | Role |
|--------|------|
| Langfuse | LLM generations, tool spans, prompt versions, run I/O |
| Postgres audit | `tool_call_audit`, `agent_runs` |
| GlitchTip | Exceptions |
| Prometheus / Grafana | API metrics |

### Product UX surfaces

Assistant · Dashboard · Customers · Issues · Tasks · Approvals · Knowledge · Evaluations · Audit · AI Governance · Admin · Settings · Account · Trust · Help.

---

## Design trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Single ReAct** vs multi-agent | Brief asks for one agent that selects tools dynamically; clearer evals | Less specialist routing than Ops supervisor |
| **pgvector** vs Qdrant | ACL + vectors in one SQL query; fewer containers | ANN scale ceiling vs dedicated vector DB |
| **Native + MCP** | Native for HITL/RBAC; MCP for research/SQL/fs | Overlap with domain tools; prefix RBAC required |
| **HITL pending approvals** | Simple stage/decide for panel demos | In-memory leftovers exist; DB `pending_approvals` for durability path |
| **Langfuse self-hosted** | Offline assessor walkthrough | Compose weight (ClickHouse/MinIO) |
| **Compose first + K8s chapter** | `make demo` satisfies brief; Ingress/NetPol/Argo show production path | Overlays thinner than Ops staging/prod |

See [`../docs/tradeoffs.md`](../docs/tradeoffs.md) and [`../docs/threat-model.md`](../docs/threat-model.md).

---

## Testing

| Layer | Command |
|-------|---------|
| Lint | `make lint` |
| API unit + coverage | `make test-coverage` (≥80%) |
| Web unit | `cd apps/web && npm test -- --run` |
| Security | `make security-audit` |
| E2E smoke | `make test-e2e` |
| Evaluation | `make eval-host` |
| Kustomize | `make kustomize-build` |

CI: Ruff, Bandit, pytest coverage, pip-audit, web lint/test/build, Gitleaks, npm audit, kustomize, e2e contract.

---

## Deep dives in this pack

| Topic | Document |
|-------|----------|
| Database design | [06-database-design.md](./06-database-design.md) |
| Agentic AI & LangGraph | [07-agentic-ai-and-langgraph.md](./07-agentic-ai-and-langgraph.md) |
| Eval results | [04-eval-results.md](./04-eval-results.md) |
| AI usage notes | [05-ai-usage-notes.md](./05-ai-usage-notes.md) |

---

## Assessment mapping

| Requirement | Location |
|-------------|----------|
| LLM agent + dynamic tools | `apps/api/agent/` — see [07](./07-agentic-ai-and-langgraph.md) |
| Reusable skills | `apps/api/skills/` |
| MCP servers (wired) | `apps/mcp-*`, `agent/mcp_client.py` |
| PostgreSQL + pgvector | `infra/postgres/`, [06](./06-database-design.md) |
| Keycloak RBAC (4 roles) | `infra/keycloak/`, `apps/api/auth/` |
| Evaluation (10 questions) | `evals/` |
| Observability | Langfuse + GlitchTip + Prometheus |
| Command Desk UX | `apps/web/` |
| GitOps | `infra/kubernetes/` (Ingress, NetworkPolicy, Argo CD) |
