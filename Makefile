.PHONY: help up down logs shell test lint build push k8s-up k8s-down chaos

DOCKER_COMPOSE = docker compose
KUBECTL = kubectl
IMAGE = eventpulse
TAG ?= latest

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Local (Docker Compose) ────────────────────────────────────────────────────
up: ## Start all services (FastAPI, Celery, Postgres, Redis, Nginx)
	$(DOCKER_COMPOSE) up -d
	@echo "API:     http://localhost"
	@echo "Docs:    http://localhost/docs"
	@echo "Metrics: http://localhost/metrics"

up-monitoring: ## Start with Prometheus + Grafana monitoring
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.monitoring.yml up -d
	@echo "Grafana:    http://localhost:3000  (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

down: ## Stop all services
	$(DOCKER_COMPOSE) down

down-v: ## Stop all services and wipe volumes (fresh DB)
	$(DOCKER_COMPOSE) down -v

logs: ## Follow all logs
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Follow FastAPI logs only
	$(DOCKER_COMPOSE) logs -f fastapi

logs-worker: ## Follow Celery worker logs only
	$(DOCKER_COMPOSE) logs -f celery-worker

ps: ## Show service status
	$(DOCKER_COMPOSE) ps

build: ## Build Docker image
	docker build -t $(IMAGE):$(TAG) .

# ── Testing ───────────────────────────────────────────────────────────────────
test: ## Run pytest
	poetry run pytest -v

test-cov: ## Run pytest with coverage
	poetry run pytest --cov=app --cov-report=term-missing --cov-report=html -v

# ── API smoke tests ───────────────────────────────────────────────────────────
smoke: ## Submit a test event and retrieve it
	@echo "=== Submitting event ==="
	@ID=$$(curl -s -X POST http://localhost/events \
		-H "Content-Type: application/json" \
		-d '{"type":"smoke.test","source":"makefile","payload":{"ts":"$(shell date +%s)"}}' \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['event_id'])") && \
	echo "Event ID: $$ID" && \
	sleep 1.5 && \
	echo "=== Fetching result ===" && \
	curl -s http://localhost/events/$$ID | python3 -m json.tool

health: ## Check /health endpoint
	@curl -s http://localhost/health | python3 -m json.tool

# ── Load testing ──────────────────────────────────────────────────────────────
load-test: ## Run normal load test (10 VUs, 5 min)
	k6 run scripts/load-test.js

spike-test: ## Run spike test (ramps to 200 VUs)
	k6 run scripts/spike-test.js

chaos-verify: ## Run continuous health checks (for use during chaos)
	k6 run scripts/chaos-verify.js

# ── Kubernetes ────────────────────────────────────────────────────────────────
minikube-start: ## Start Minikube cluster
	minikube start --cpus=4 --memory=4096 --driver=docker
	minikube addons enable ingress
	minikube addons enable metrics-server
	eval $$(minikube docker-env) && docker build -t eventpulse:latest .

k8s-apply: ## Apply all K8s manifests
	bash scripts/k8s-apply.sh

k8s-status: ## Show all K8s resource status
	$(KUBECTL) get pods,services,hpa,ingress

k8s-logs: ## Follow FastAPI pod logs
	$(KUBECTL) logs -l app=fastapi -f

k8s-down: ## Delete all K8s resources
	$(KUBECTL) delete -f k8s/ --ignore-not-found=true

# ── Terraform ─────────────────────────────────────────────────────────────────
tf-init: ## Terraform init
	cd terraform && terraform init

tf-plan: ## Terraform plan
	cd terraform && terraform plan

tf-apply: ## Terraform apply (provisions AWS infrastructure)
	cd terraform && terraform apply

tf-destroy: ## Terraform destroy (removes all AWS resources — stops billing)
	cd terraform && terraform destroy

# ── Git ───────────────────────────────────────────────────────────────────────
new-feature: ## Start a new feature branch. Usage: make new-feature BRANCH=feature/backend-xyz
	git checkout develop && git pull && git checkout -b $(BRANCH)
