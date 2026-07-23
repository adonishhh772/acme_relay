# Deliverable 4 — Evaluation Results

## Suite overview

The evaluation set contains **10 questions** covering tool selection, groundedness, RBAC enforcement, ACL RAG, and next-action / HITL quality. Questions live in [`../evals/eval_questions.json`](../evals/eval_questions.json).

| Metric | Description |
|--------|-------------|
| **Tool selection** | Expected tools invoked for the query |
| **Groundedness** | Response tied to tool evidence (case keys / accounts) |
| **RBAC** | Role-based access respected (deny / approval flows) |
| **Next actions** | Support stages HITL; sales cannot create actions |
| **ACL RAG** | Sales must not see restricted executive knowledge |

### Roles exercised

| Role | User | Scenarios |
|------|------|-----------|
| `sales_user` | `alice` / `alice123` | Read-heavy; write denied; restricted RAG hidden |
| `support_user` | `bob` / `bob123` | Full read; writes stage HITL |
| `admin` | `admin` / `admin123` | Restricted knowledge allowed |

Demo accounts: **VaultLedger Payments**, **Nexus Freight**, **Aurora Bank** (`OPS-3101`–`OPS-3103`).

---

## How to run

```bash
make demo
make migrate-db
make eval-host
# or: make eval   (inside API container)
```

Results:

- `evals/results.json` — machine-readable (when live run completes)
- `evals/eval_results.md` — human-readable summary
- Admin UI: https://acme-relay.local/evaluations — **Run suite** runs live chat turns and shows **Step 1…N** progress (`POST /api/evaluations/run`, poll `GET /api/evaluations/run/status`, history via `GET /api/evaluations/runs`)

**Important:** Eval runner obtains JWTs from Keycloak. `KEYCLOAK_URL` / issuer must match the API, or requests fail with `401 Invalid token issuer`.

---

## Suite design (checked-in baseline)

| ID | Role | Expected tools | RBAC / notes |
|----|------|----------------|--------------|
| eval_01 | sales_user | get_open_issues / escalation / summarize | Primary VaultLedger demo flow |
| eval_02 | sales_user | create_next_action | **Must deny** — sales cannot mutate |
| eval_03 | support_user | get_open_issues | Nexus Freight open issues |
| eval_04 | support_user | summarize_issue_history | OPS-3101 status |
| eval_05 | support_user | run_escalation_summary_skill | Escalation skill |
| eval_06 | sales_user | search_knowledge | Restricted protocol **must not leak** |
| eval_07 | admin | search_knowledge | Restricted knowledge allowed |
| eval_08 | support_user | SLA skill / get_open_issues | SLA breach assessment |
| eval_09 | sales_user | get_customer_profile_by_name | Aurora Bank owner |
| eval_10 | support_user | create_next_action | Stages HITL approval |

---

## Commentary

### What “good” looks like

1. **Tool selection** — Agent must call DB/RAG tools; never invent VaultLedger/Nexus Freight facts.
2. **Groundedness** — Answers cite `OPS-*` keys and seeded owners present in tool outputs; API also runs `verify_groundedness` on every chat.
3. **RBAC** — Sales `create_next_action` → permission_denied; support stages pending approvals.
4. **ACL RAG** — `allowed_roles` filter runs **before** vector ranking; sales queries for executive protocol must not return restricted chunks.
5. **HITL** — Support next actions appear in Approvals; admin decides.

### Known harness notes

- Live scores depend on LLM availability and Keycloak issuer alignment.
- Deterministic embedding fallback may reduce RAG ranking quality without `OPENAI_API_KEY`.
- Re-run after stack changes: `make eval-host` and refresh this document from `evals/eval_results.md`.

### Latest checked-in design artifact

See [`../evals/eval_results.md`](../evals/eval_results.md) for the suite design commentary committed with the repo. Replace the “Latest recorded run” section after a live panel dry-run and paste pass rates here.

| Metric | Target for panel |
|--------|------------------|
| Pass rate | ≥ 8/10 with API keys configured |
| RBAC cases (02, 06, 10) | Must pass |
| Avg latency | Record p50/p95 from harness |

---

## Mapping to product features

| Eval theme | Product feature |
|------------|-----------------|
| Tool use | Native tools + skills + MCP |
| Groundedness | `agent/groundedness.py` + `agent_runs.groundedness_*` |
| RBAC | `auth/rbac.py` + Keycloak roles |
| ACL RAG | `knowledge/search.py` + pgvector |
| HITL | `/api/approvals` + Approvals page |
