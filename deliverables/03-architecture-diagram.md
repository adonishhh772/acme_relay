# Deliverable 3 — Architecture Diagram

## System-level diagram

Open [`03-architecture-diagram.mmd`](./03-architecture-diagram.mmd) in any Mermaid-compatible viewer (GitHub, VS Code Mermaid extension, https://mermaid.live).

```mermaid
flowchart TB
  subgraph clients [Clients]
    Web["apps/web<br/>React Command Desk"]
    ExtMCP["External MCP Clients<br/>Cursor / Claude Desktop"]
  end

  subgraph auth [Identity]
    KC["Keycloak<br/>JWT / TOTP / 4 roles"]
  end

  subgraph api [apps/api — FastAPI]
    direction TB
    Routers["HTTP Routers<br/>chat · desk · tasks · approvals · knowledge<br/>admin · account · evaluations · governance · mcp/status"]
    Agent["LangGraph ReAct<br/>create_react_agent"]
    Tools["Native Tools<br/>RBAC · HITL · audit"]
    Skills["Skills ×4<br/>escalation · SLA · triage · handoff"]
    Ground["Groundedness Verifier"]
    MCPClient["MCP Client<br/>langchain-mcp-adapters"]
    Routers --> Agent
    Agent --> Tools
    Agent --> Skills
    Agent --> MCPClient
    Agent --> Ground
  end

  subgraph mcp [MCP Servers — SSE]
    DomainMCP["mcp-domain :8090"]
    FsMCP["mcp-filesystem :8091"]
    PgMCP["mcp-postgres :8092<br/>SELECT only"]
  end

  subgraph data [Data Stores]
    PG[("PostgreSQL 16 + pgvector<br/>customers · cases · audit · RBAC · RAG chunks")]
    Redis[("Redis Stack<br/>sessions · checkpoints · Celery broker")]
    KB["infra/knowledge/*.md<br/>public · internal · restricted"]
  end

  subgraph workers [Async]
    Celery["Celery Worker<br/>chunk + embed ingest"]
  end

  subgraph obs [Observability]
    Langfuse["Langfuse"]
    GlitchTip["GlitchTip"]
    Prom["Prometheus"]
    Grafana["Grafana"]
  end

  Web -->|"HTTPS + Bearer JWT"| Routers
  Web -->|"OIDC login"| KC
  Routers -->|"validate JWT"| KC

  Tools --> PG
  Tools --> Redis
  MCPClient --> DomainMCP
  MCPClient --> FsMCP
  MCPClient --> PgMCP
  ExtMCP --> mcp

  DomainMCP --> PG
  FsMCP --> KB
  PgMCP --> PG
  Celery --> KB
  Celery --> PG

  Agent --> Langfuse
  Routers --> Prom
  Prom --> Grafana
  Agent -->|"agent_runs · tool_call_audit"| PG
```

Also see the compact in-repo diagram: [`../docs/architecture-diagram.mmd`](../docs/architecture-diagram.mmd).

---

## Data flow summary

### 1. Authentication

```text
User → Keycloak (OIDC + optional TOTP) → JWT
  → Web stores token → API validates issuer + realm roles
  → sales_user | support_user | operations_user | admin
```

### 2. Chat / agent

```text
POST /api/chat
  → RBAC ToolContext
  → LangGraph ReAct (native + skills + MCP)
  → tool_call_audit (source native|mcp)
  → verify_groundedness
  → persist agent_runs
  → ChatResponse + groundedness payload
```

### 3. Dashboard

```text
GET /api/desk/summary
  → open/critical cases, pending actions, SLA risk, tasks, groundedness rate
  → role_scope returned for UI
```

### 4. RAG knowledge

```text
Markdown under infra/knowledge/{public,internal,restricted}/
  → POST /api/knowledge/ingest → Celery
  → chunk + embed → knowledge_chunks (pgvector + allowed_roles)
  → search_knowledge: roles filter THEN vector distance
```

### 5. Observability

```text
Chat request
  → Langfuse CallbackHandler + tool spans
  → Prometheus /metrics
  → GlitchTip on exceptions
  → Postgres agent_runs / tool_call_audit mirror
```

### 6. GitOps

```text
Git → Argo CD Application → kustomize base
  (api, worker, web, MCP, Ingress, NetworkPolicies)
```

---

## Security boundaries

| Boundary | Control |
|----------|---------|
| Browser → API | Keycloak JWT, CORS; Ingress TLS in K8s |
| API → tools | `PERMISSIONS` + MCP prefix map + HITL |
| MCP postgres | SELECT-only keyword blocklist; support/ops/admin only |
| RAG | `allowed_roles && user_roles` before ranking |
| Cluster | Default-deny NetworkPolicy; API→MCP allowlist |
| LLM keys | Server-side only |

See [`../docs/threat-model.md`](../docs/threat-model.md).
