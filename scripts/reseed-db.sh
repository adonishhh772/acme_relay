#!/usr/bin/env bash
# Reset and reload Relay demo data into PostgreSQL (safe to re-run).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Ensuring Postgres is running..."
docker compose up -d postgres
docker compose exec -T postgres sh -c 'until pg_isready -U relay -d relay_ops; do sleep 1; done'

echo "==> Applying account-management migration..."
docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/05-account-management.sql

echo "==> Truncating business tables..."
docker compose exec -T postgres psql -U relay -d relay_ops <<'EOF'
TRUNCATE
  issue_updates,
  next_actions,
  issues,
  knowledge_chunks,
  knowledge_documents,
  user_roles,
  users,
  customers,
  metric_snapshots
RESTART IDENTITY CASCADE;
EOF

echo "==> Reloading seed data..."
docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/seed.sql
docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/06-am-metrics-seed.sql

echo "==> Demo data summary:"
docker compose exec -T postgres psql -U relay -d relay_ops -c "
SELECT c.external_id, c.name, c.contract_value_gbp, c.renewal_date,
       COUNT(i.id) FILTER (WHERE i.status IN ('open','in_progress')) AS active_issues
FROM customers c
LEFT JOIN issues i ON i.customer_id = c.id
GROUP BY c.external_id, c.name, c.contract_value_gbp, c.renewal_date
ORDER BY c.external_id;
"

echo "==> Metrics samples:"
docker compose exec -T postgres psql -U relay -d relay_ops -c "
SELECT metric_name, count(*) AS points
FROM metric_snapshots
GROUP BY metric_name
ORDER BY metric_name;
"

echo "==> Done. Flagship: VAULTLEDGER / OPS-3101"
