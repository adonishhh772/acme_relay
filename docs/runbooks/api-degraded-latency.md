# Runbook: API degraded latency

## Symptoms

- Chat `latency_ms` elevated in `agent_runs`
- Grafana / Prometheus scrape shows high request duration

## Checks

1. Langfuse trace: LLM vs tool time breakdown
2. Redis health (checkpoints / sessions)
3. Postgres slow queries (`pg_stat_activity`)
4. OpenAI rate limits / embedding latency for knowledge ingest

## Mitigations

- Scale `relay-api` replicas behind Ingress
- Reduce concurrent Celery ingest
- Prefer cached Redis session reads; avoid unnecessary MCP postgres exploratory queries
