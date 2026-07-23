.PHONY: up down demo logs eval lint test test-coverage quality reseed-db migrate-db kustomize-build security-audit test-e2e deliverables-zip tls-certs tls-up tls-down

COMPOSE_TLS := docker compose -f docker-compose.yml -f docker-compose.tls.yml

up:
	docker compose up --build -d

down:
	docker compose down

demo: up
	@echo "Relay Command Desk → http://localhost:5173"
	@echo "API docs          → http://localhost:8000/docs"
	@echo "MCP status        → http://localhost:8000/api/mcp/status (auth required)"
	@echo "Keycloak          → http://localhost:8080"
	@echo "  alice/alice123 sales · bob/bob123 support · dana/dana123 operations · admin/admin123"
	@echo "HTTPS (optional): make tls-certs && make tls-up  → https://acme-relay.local"

tls-certs:
	chmod +x scripts/setup-local-tls.sh
	./scripts/setup-local-tls.sh

tls-up: tls-certs
	$(COMPOSE_TLS) up --build -d
	@echo "Command Desk → https://acme-relay.local"
	@echo "API docs     → https://api.acme-relay.local/docs"
	@echo "Keycloak     → https://auth.acme-relay.local"
	@echo "GlitchTip    → https://glitchtip.local"
	@echo "Langfuse     → https://langfuse.local"
	@echo "Grafana      → https://grafana.local"
	@echo "Docs         → docs/local-https.md"

tls-down:
	$(COMPOSE_TLS) down

logs:
	docker compose logs -f api worker

reseed-db:
	bash scripts/reseed-db.sh

migrate-db:
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/03-schema-enrichment.sql
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/04-rbac-operations-parity.sql
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/05-account-management.sql
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/06-am-metrics-seed.sql
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/07-knowledge-business-value.sql

eval:
	docker compose exec -e API_URL=http://localhost:8000 -e KEYCLOAK_URL=http://localhost:8080 api \
		python /app/evals/run_eval.py

eval-host:
	cd evals && API_URL=http://127.0.0.1:8000 KEYCLOAK_URL=http://localhost:8080 \
		python3 run_eval.py
	@echo "Note: KEYCLOAK_URL must be http://localhost:8080 (not 127.0.0.1) so JWT iss matches the API."

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

