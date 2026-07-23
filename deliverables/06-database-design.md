# Deliverable 6 — Database Design (PostgreSQL)

Detailed schema reference for **Relay**. PostgreSQL 16 + **pgvector** is the durable store for operational data, audit, RBAC, and ACL-aware knowledge chunks. Ephemeral chat turns and LangGraph checkpoints live in Redis; Celery uses Redis as broker.

---

## Environment

| Setting | Value |
|---------|-------|
| **Database name** | `relay_ops` |
| **Docker connection** | `postgresql://relay:relay_secret@postgres:5432/relay_ops` |
| **Extensions** | `pgcrypto`, `vector` |
| **Migration source** | `infra/postgres/*.sql` |
| **Version tracking** | `schema_migrations` |

### Apply order

| File | Purpose |
|------|---------|
| `00-databases.sh` | Extra DBs (e.g. GlitchTip) |
| `init.sql` | Core schema + enums (incl. `operations_user`) |
| `seed.sql` | VaultLedger / Nexus Freight / Aurora Bank |
| `03-schema-enrichment.sql` | Idempotent backfill for existing volumes |
| `04-rbac-operations-parity.sql` | RBAC tables, tenant columns, tasks, CSAT |

```bash
make migrate-db
```

---

## Design principles

1. **Referential integrity** — Issues reference customers; chunks nexus freight with documents.
2. **RBAC dual-layer** — Keycloak JWT at runtime + `permissions` / `rbac_roles` tables for admin UX.
3. **ACL before ANN** — Knowledge search filters `allowed_roles` then orders by embedding distance.
4. **Audit by design** — Every tool call lands in `tool_call_audit` with `source`.
5. **Groundedness persisted** — `agent_runs.groundedness_passed` / `groundedness_explanation`.
6. **Tenant-ready** — `organization_id` on users, customers, knowledge, tasks (default org `acme-ops`).

---

## Data store boundaries

| Store | Technology | Contents |
|-------|------------|----------|
| **Operational + RAG** | PostgreSQL + pgvector | Customers, cases, RBAC, audit, knowledge chunks |
| **Session / graph / queue** | Redis Stack | Chat turns, LangGraph checkpoints, Celery broker |
| **Identity** | Keycloak | JWT issuance, realm roles |
| **Files** | `infra/knowledge/` | Source markdown for ingest |

Unlike Ops (Qdrant for vectors), Relay keeps embeddings **in Postgres** next to ACL metadata.

---

## Domain overview

```text
┌─────────────────────────────────────────────────────────────────┐
│  CORE OPERATIONS          │  IDENTITY & TENANCY                   │
│  customers                │  organizations                        │
│  issues                   │  users, user_roles                    │
│  issue_updates            │  permissions, rbac_roles              │
│  next_actions             │  role_permissions                     │
│  user_tasks               │  user_role_assignments                │
├───────────────────────────┼───────────────────────────────────────┤
│  AGENT & AUDIT            │  KNOWLEDGE (pgvector)                 │
│  agent_runs               │  knowledge_documents                  │
│  tool_call_audit          │  knowledge_chunks.embedding           │
│  pending_approvals        │                                       │
│  prompt_versions          │                                       │
│  eval_runs                │                                       │
├───────────────────────────┼───────────────────────────────────────┤
│  ANALYTICS & FEEDBACK     │  META                                 │
│  metric_snapshots         │  schema_migrations                    │
│  issue_csat_responses     │                                       │
│  chat_feedback_events     │                                       │
└───────────────────────────┴───────────────────────────────────────┘
```

---

## Entity-relationship diagrams

### Core operations + tenancy

```mermaid
erDiagram
    organizations ||--o{ customers : scopes
    organizations ||--o{ users : employs
    customers ||--o{ issues : has
    issues ||--o{ issue_updates : has
    issues ||--o{ next_actions : has
    organizations ||--o{ user_tasks : scopes

    customers {
        uuid id PK
        uuid organization_id FK
        varchar external_id UK
        varchar name
        varchar tier
        bool is_active
    }

    issues {
        uuid id PK
        uuid customer_id FK
        varchar issue_key UK
        issue_status status
        issue_priority priority
        timestamptz sla_due_at
    }

    issue_updates {
        uuid id PK
        uuid issue_id FK
        varchar author
        text body
        bool is_internal
    }

    next_actions {
        uuid id PK
        uuid issue_id FK
        text action_text
        next_action_status status
    }

    user_tasks {
        uuid id PK
        varchar keycloak_sub
        uuid organization_id FK
        text title
        varchar status
        varchar priority
    }
```

### RBAC

```mermaid
erDiagram
    permissions ||--o{ role_permissions : granted
    rbac_roles ||--o{ role_permissions : has
    rbac_roles ||--o{ user_role_assignments : assigned
    users ||--o{ user_role_assignments : receives
    organizations ||--o{ user_role_assignments : scopes

    permissions {
        uuid id PK
        varchar key UK
        varchar category
    }

    rbac_roles {
        uuid id PK
        varchar slug
        varchar keycloak_role_name
        bool is_system
    }
```

### Knowledge (ACL RAG)

```mermaid
erDiagram
    organizations ||--o{ knowledge_documents : scopes
    knowledge_documents ||--o{ knowledge_chunks : contains

    knowledge_documents {
        uuid id PK
        varchar title
        varchar source_path
        knowledge_sensitivity sensitivity
        app_role_array allowed_roles
        uuid organization_id FK
    }

    knowledge_chunks {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content
        vector embedding
        app_role_array allowed_roles
    }
```

### Agent audit

```mermaid
erDiagram
    agent_runs {
        uuid id PK
        varchar request_id
        text query
        text answer
        text_array tools_used
        bool groundedness_passed
        text groundedness_explanation
        int latency_ms
    }

    tool_call_audit {
        uuid id PK
        varchar request_id
        varchar tool_name
        jsonb arguments
        text result_summary
        varchar source
        bool success
    }
```

---

## Enums

| Enum | Values |
|------|--------|
| `app_role` | `sales_user`, `support_user`, `operations_user`, `admin` |
| `issue_status` | `open`, `in_progress`, `resolved`, `closed` |
| `issue_priority` | `low`, `medium`, `high`, `critical` |
| `next_action_status` | `pending`, `approved`, `completed`, `rejected` |
| `knowledge_sensitivity` | `public`, `internal`, `restricted` |

---

## Critical query: ACL RAG

```sql
SELECT c.id, c.content, c.sensitivity, d.title
FROM knowledge_chunks c
JOIN knowledge_documents d ON d.id = c.document_id
WHERE c.allowed_roles && $2::app_role[]
ORDER BY c.embedding <=> $1::vector
LIMIT $3;
```

Filter **before** ranking — never retrieve then discard in the prompt.

---

## Seed narrative

| Account | External ID | Flagship case |
|---------|-------------|---------------|
| VaultLedger Payments | `VAULTLEDGER` | OPS-3101 critical settlement |
| Nexus Freight | `NEXUSFREIGHT` | OPS-3102 webhooks |
| Aurora Bank | `AURORABANK` | OPS-3103 POD delay |

Knowledge tiers: public SLA (all roles), internal playbook (support/ops/admin), restricted executive (admin).

---

## Indexes (selected)

- `issues(customer_id)`, `issues(status)`, `issues(priority)`
- GIN on `knowledge_chunks.allowed_roles`
- `tool_call_audit(request_id)`, `tool_call_audit(source)`
- `agent_runs(groundedness_passed)`
- `user_tasks(keycloak_sub, status)`

---

## Related docs

- Short schema index: [`../docs/database-schema.md`](../docs/database-schema.md)
- Threat model: [`../docs/threat-model.md`](../docs/threat-model.md)
