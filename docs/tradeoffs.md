# Design trade-offs

## PostgreSQL vs NoSQL

Chose Postgres as system of record because Acme’s domain is relational (accounts → cases → updates → next actions), needs ACID when approving actions, and RBAC-aware RAG benefits from ACL columns + vectors in one SQL query. Redis is used deliberately for ephemeral session/queue state — polyglot by purpose.

## pgvector vs Qdrant

RAG is required in this build; a dedicated vector DB is not. pgvector keeps embeddings next to ACL metadata, cuts a container, and matches mid-size knowledge corpora. Qdrant remains a later option if corpus/QPS outgrows OLTP Postgres.

## Single ReAct vs multi-agent

The brief asks for one agent that dynamically selects tools. A supervisor/multi-agent graph can obscure tool selection and hurt eval clarity, so Relay ships a single ReAct loop with MCP tools merged into the same tool list.

## Native tools vs MCP

Native tools own HITL/RBAC/audit for mutations. MCP adds parallel research paths (domain/filesystem/postgres) loaded via SSE adapters. Postgres MCP is restricted to support/admin.

## Langfuse vs LangSmith

Self-hosted Langfuse keeps traces and prompt versions local for the panel demo. It adds Compose weight; that cost is accepted for offline assessor walkthroughs.

## Compose vs Kubernetes

`docker compose up` satisfies the brief. K8s + Argo CD demonstrate production GitOps and horizontal scaling without making kind a hard dependency for the primary demo. Ingress and NetworkPolicies are part of the base kustomization so the GitOps chapter shows real traffic and isolation controls.
