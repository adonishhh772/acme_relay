# Deliverable 1 — Repository Access

## GitHub repository

The complete source code and configuration for **Relay (Command Desk)** live in this tree.

| Item | Details |
|------|---------|
| **Repository root** | `acme-relay/` (this workspace) |
| **Primary branch** | Check with `git branch --show-current` |
| **Remote** | Prefer promoting this directory to its own Git remote for submission (`git remote add origin <url>`) |

### What is included

```
acme-relay/
├── apps/
│   ├── api/                 # FastAPI + LangGraph ReAct, desk, tasks, admin, governance
│   ├── worker/              # Celery knowledge ingest
│   ├── mcp-domain/          # Domain MCP (SSE)
│   ├── mcp-filesystem/      # Filesystem MCP
│   ├── mcp-postgres/        # SELECT-only Postgres MCP
│   └── web/                 # React Command Desk (dashboard, assistant, trust/help)
├── infra/
│   ├── postgres/            # Schema, enrichment, RBAC parity, seed
│   ├── keycloak/            # Realm export (4 roles + TOTP)
│   ├── knowledge/           # ACL-tiered markdown (public/internal/restricted)
│   ├── prometheus/
│   └── kubernetes/          # Ingress, NetworkPolicies, MCP Deployments, Argo CD
├── evals/                   # 10-question evaluation suite
├── docs/                    # Architecture, threat model, runbooks, CONTRIBUTING
├── deliverables/            # This submission pack
├── docker-compose.yml       # Full local stack
├── docker-compose.e2e.yml   # Playwright smoke stack
├── Makefile                 # demo, quality, migrate-db, eval, e2e, deliverables-zip
├── .env.example             # Environment template (no secrets)
└── .github/workflows/ci.yml # Ruff, Bandit, coverage, audits, kustomize, e2e contract
```

### Secrets and excluded files

Not committed (see `.gitignore`):

- `.env` — local secrets and API keys
- `infra/kubernetes/base/secret.yaml` — real K8s secrets (use `secret.example.yaml`)
- `.venv/`, `node_modules/`, `dist/`, coverage artifacts

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` for best LLM/embedding quality.

---

## Zip archive (alternative submission)

```bash
# From acme-relay/
make deliverables-zip
```

Or manually:

```bash
cd /path/to/acme-relay
git archive --format=zip --output=deliverables/relay-command-desk-source.zip HEAD
```

The archive must include `docker-compose.yml`, `.env.example`, `Makefile`, and all source under `apps/` and `infra/`.

---

## Verification checklist

1. `cp .env.example .env` and set `OPENAI_API_KEY` (or accept hash embeddings offline).
2. `make demo` then `make migrate-db`.
3. Open http://localhost:5173 — sign in (`bob` / `bob123` or `dana` / `dana123`).
4. `make quality` — lint + API coverage ≥80%.
5. `make eval-host` — 10-question suite (stack must be running).
6. Optional: `GET /api/mcp/status` (auth) confirms MCP agent tool load.
