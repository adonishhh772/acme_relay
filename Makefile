.PHONY: up down demo logs eval lint test test-coverage quality reseed-db migrate-db kustomize-build security-audit test-e2e deliverables-zip

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

logs:
	docker compose logs -f api worker

reseed-db:
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/seed.sql

migrate-db:
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/03-schema-enrichment.sql
	docker compose exec -T postgres psql -U relay -d relay_ops < infra/postgres/04-rbac-operations-parity.sql

eval:
	docker compose exec -e API_URL=http://127.0.0.1:8000 -e KEYCLOAK_URL=http://keycloak:8080 api \
		python /app/evals/run_eval.py

eval-host:
	cd evals && API_URL=http://127.0.0.1:8000 KEYCLOAK_URL=http://127.0.0.1:8080 \
		python3 run_eval.py

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

