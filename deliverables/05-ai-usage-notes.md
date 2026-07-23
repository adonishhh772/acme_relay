# Deliverable 5 — AI Usage Notes

A brief account of how AI-assisted development tools were used while building **Relay (Command Desk)**.

---

## Tools used

| Tool | Role in development |
|------|---------------------|
| **Cursor IDE (Agent mode)** | Primary coding assistant — scaffolding, refactors, tests, multi-file parity work |
| **OpenAI API** | Runtime inference for the product (chat agent + embeddings) |
| **Langfuse** | Trace and debug agent behaviour during development |
| **Inline completion** | Boilerplate and repetitive patterns inside Cursor |

No customer data or production secrets were sent to AI tools. Local development uses seeded demo data only (VaultLedger / Nexus Freight / Aurora Bank).

---

## Where AI assisted development

### 1. Agent and tool layer (`apps/api/agent/`)

- LangGraph `create_react_agent` wiring and Redis checkpoint patterns
- MCP client (`langchain-mcp-adapters`) + `wrap_mcp_tools_for_context`
- Groundedness verifier against case/account claims
- Tool router audit (`source` = native \| mcp)

**Human-reviewed:** RBAC matrix, HITL staging, MCP prefix permissions (`mcp_read` / `mcp_sql`), sales deny paths.

### 2. Command Desk UX (`apps/web/`)

- Route surface parity with Operations (dashboard, tasks, admin, account, trust/help)
- RBAC nav helpers and Vitest coverage
- Playwright smoke scaffolding

UI drafts were adjusted for Relay’s CSS shell, `data-testid`s, and role-gated navigation.

### 3. Data & RBAC (`infra/postgres/`)

- Idempotent enrichment SQL (`03`, `04`) for RBAC tables, `operations_user`, tasks, CSAT
- Seed uniqueness and ACL knowledge tiers

Migrations were **manually reviewed** for enum adds, idempotency, and org resolution via `slug = 'acme-ops'`.

### 4. Infra, CI, deliverables

- Kubernetes Ingress / NetworkPolicy / MCP Deployments
- CI jobs (Bandit, Gitleaks, coverage, kustomize, e2e contract)
- This deliverables pack (structure mirrored from assessment expectations)

---

## What was not delegated to AI

| Area | Reason |
|------|--------|
| **Security / RBAC rules** | Defined in `auth/rbac.py` + Keycloak realm; validated with tests |
| **Secrets** | Never committed; `secret.example.yaml` uses placeholders |
| **Production networking** | NetworkPolicies and `expose` (not public DB ports) human-checked |
| **Eval pass criteria** | Authored in `evals/eval_questions.json` from requirements |
| **Final architecture sign-off** | Trade-offs documented; live eval re-run required before panel |

---

## Runtime AI (the product)

Relay **is** an AI system. Runtime LLM usage includes:

- **Chat agent** — LangGraph ReAct with native tools, skills, and MCP tools
- **Skills** — Escalation, SLA breach, triage, shift handoff
- **Embeddings** — OpenAI `text-embedding-3-small` into pgvector (hash fallback offline)
- **Groundedness** — Post-answer verification against tool corpus (not LLM-as-judge)

---

## Quality practices with AI-generated code

1. Run `make quality` before considering a change done.
2. Prefer tests with `data-testid` and mocked I/O (no real DB in unit tests).
3. Never accept generated “eval passed” artifacts without `make eval-host`.
4. Keep prompts versioned (`apps/api/prompts/relay-system.yaml`) with CI gate.
5. Treat AI output as a draft — especially auth, migrations, and NetworkPolicies.
