# Production readiness checklist

## Must have before production traffic

- [ ] Replace demo Keycloak (`start-dev`) with HA Keycloak + external DB + TLS
- [ ] Rotate all secrets (≥32 char); never commit real `secret.yaml`
- [ ] Ingress TLS via cert-manager; disable host-port binds for Postgres/Redis
- [ ] NetworkPolicies applied (default deny + allowlists)
- [ ] Managed Postgres with backups; run `make migrate-db` in release pipeline
- [ ] MCP tools verified via `GET /api/mcp/status` in staging
- [ ] Groundedness failure rate monitored (Langfuse + `agent_runs.groundedness_passed`)
- [ ] Celery workers sized for ingest backlog; Redis persistence reviewed
- [ ] CI green on main (ruff, pytest ≥80%, web tests, kustomize validate)

## Should have

- [ ] Argo CD Application pointed at real `repoURL`
- [ ] HPA for `relay-api` / `relay-web`
- [ ] External Secrets / sealed secrets
- [ ] Load / soak test of chat + RAG
- [ ] Durable HITL path fully migrated off any in-memory leftovers
- [ ] Prompt promotion process (see governance UI + `prompt_versions`)

## Nice to have

- [ ] OpenTelemetry → Tempo/Jaeger in addition to Langfuse
- [ ] Postgres RLS for multi-tenant hard isolation
- [ ] Playwright e2e smoke in CI
