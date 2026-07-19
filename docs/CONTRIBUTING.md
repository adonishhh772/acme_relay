# Contributing to Relay

## Prerequisites

```bash
cd acme-relay
python3 -m venv apps/api/.venv
apps/api/.venv/bin/pip install -r apps/api/requirements-dev.txt bandit pip-audit
cd apps/web && npm install && npx playwright install chromium
```

## Quality bar

| Command | Purpose |
|---------|---------|
| `make lint` | Ruff (API) + ESLint (web) |
| `make test` | API pytest + Vitest |
| `make test-coverage` | API coverage **≥80%** |
| `make security-audit` | Bandit + pip-audit + npm audit |
| `make kustomize-build` | Validate Ingress + NetworkPolicy |
| `make migrate-db` | Apply schema enrichment + RBAC parity |
| `make test-e2e` | Playwright smoke via `docker-compose.e2e.yml` |
| `make quality` | lint + coverage |

## Merge requirements (CI)

`.github/workflows/ci.yml` jobs:

1. Prompt version gate
2. Ruff + Bandit + pytest ≥80% + pip-audit
3. Web lint + Vitest + production build
4. Gitleaks + npm audit (high)
5. Kustomize validate (Ingress + NetworkPolicy)
6. E2E smoke contract (spec + health path)

## Local demo

```bash
cp .env.example .env
make demo
make migrate-db
```

Users: `alice` (sales), `bob` (support), `dana` (operations), `admin`.

## Commit messages

Prefer imperative summaries. With task IDs: `[TASK-123]: short imperative summary`.
