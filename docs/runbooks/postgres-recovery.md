# Runbook: Postgres recovery

## Symptoms

- API `/health/ready` degraded or chat 500s
- Worker ingest failing

## Recovery

1. Confirm volume / PVC health
2. Restore from backup into a new instance
3. Re-apply schema: `init.sql` (empty) or `make migrate-db` (existing)
4. Re-seed demo data only in non-prod: `make reseed-db`
5. Re-run knowledge ingest from Command Desk

Never expose Postgres ports on `0.0.0.0` in production — use `expose` / ClusterIP only.
