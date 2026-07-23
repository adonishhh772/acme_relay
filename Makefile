.PHONY: up down demo up-http demo-http logs eval lint test test-coverage quality reseed-db migrate-db kustomize-build security-audit test-e2e deliverables-zip tls-certs tls-up tls-down

COMPOSE := docker compose -f docker-compose.yml -f docker-compose.tls.yml
COMPOSE_HTTP := docker compose -f docker-compose.yml

up: tls-certs
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

demo: up
	@echo ""
	@echo "Relay Command Desk (HTTPS)"
	@echo "  Desk       → https://acme-relay.local"
	@echo "  API docs   → https://api.acme-relay.local/docs"
	@echo "  Keycloak   → https://auth.acme-relay.local"
	@echo "  GlitchTip  → https://glitchtip.local"
	@echo "  Langfuse   → https://langfuse.local"
	@echo "  Grafana    → https://grafana.local"
	@echo "  Users      → alice/alice123 · bob/bob123 · dana/dana123 · admin/admin123"
	@echo "  Docs       → docs/local-https.md"
	@echo "  HTTP-only  → make demo-http  (localhost ports, no Caddy)"

# Escape hatch: plain localhost HTTP (no mkcert / Caddy)
up-http:
	$(COMPOSE_HTTP) up --build -d

demo-http: up-http
	@echo "Relay Command Desk → http://localhost:5173"
	@echo "API docs          → http://localhost:8000/docs"
	@echo "Keycloak          → http://localhost:8080"
	@echo "  alice/alice123 sales · bob/bob123 support · dana/dana123 operations · admin/admin123"

tls-certs:
	chmod +x scripts/setup-local-tls.sh
	./scripts/setup-local-tls.sh

tls-up: demo

tls-down: down

logs:
	$(COMPOSE) logs -f api worker

reseed-db:
	bash scripts/reseed-db.sh

migrate-db:
	$(COMPOSE) exec -T postgres psql -U relay -d relay_ops < infra/postgres/03-schema-enrichment.sql
	$(COMPOSE) exec -T postgres psql -U relay -d relay_ops < infra/postgres/04-rbac-operations-parity.sql
	$(COMPOSE) exec -T postgres psql -U relay -d relay_ops < infra/postgres/05-account-management.sql
	$(COMPOSE) exec -T postgres psql -U relay -d relay_ops < infra/postgres/06-am-metrics-seed.sql
	$(COMPOSE) exec -T postgres psql -U relay -d relay_ops < infra/postgres/07-knowledge-business-value.sql
	$(COMPOSE) exec -T postgres psql -U relay -d relay_ops < infra/postgres/08-ingest-ops-admin-only.sql

eval:
	$(COMPOSE) exec -e API_URL=http://api:8000 -e KEYCLOAK_URL=http://keycloak:8080 -e KEYCLOAK_ISSUER=https://auth.acme-relay.local api \
		python /app/evals/run_eval.py

eval-host:
	cd evals && API_URL=https://api.acme-relay.local KEYCLOAK_URL=https://auth.acme-relay.local \
		SSL_CERT_FILE="$$(mkcert -CAROOT)/rootCA.pem" \
		python3 run_eval.py
	@echo "Note: JWT iss must be https://auth.acme-relay.local (matches make demo TLS)."

argocd-apply:
	kubectl apply -k infra/kubernetes/base
	kubectl apply -f infra/kubernetes/platform/argo-cd/applications.yaml

kustomize-build:
	kubectl kustomize infra/kubernetes/base

lint:
	cd apps/api && ruff check . && ruff format --check .
	cd apps/web && npm run lint

test:
	cd apps/api && pytest -q
	cd apps/web && npm test -- --run

test-coverage:
	cd apps/api && pytest --cov=. --cov-config=.coveragerc --cov-fail-under=80 --cov-report=term-missing

security-audit:
	cd apps/api && bandit -q -r . -x tests -lll || true
	pip-audit -r apps/api/requirements.txt || true
	cd apps/web && npm audit --audit-level=high || true

test-e2e:
	docker compose -f docker-compose.e2e.yml up --build -d --wait || docker compose -f docker-compose.e2e.yml up --build -d
	cd apps/web && npx playwright test --project=chromium --workers=1
	docker compose -f docker-compose.e2e.yml down

quality: lint test-coverage

deliverables-zip:
	chmod +x scripts/package-deliverables-zip.sh
	./scripts/package-deliverables-zip.sh
	@ls -lh deliverables/relay-command-desk-source.zip
	@echo "Deliverables pack → deliverables/README.md"
