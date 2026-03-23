# EventPulse — Production-Grade Event Processing Platform

> A containerized, auto-scaling, monitored backend system built to simulate real production workloads.

[![CI](https://github.com/markkungu/eventpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/markkungu/eventpulse/actions)

---

## What Is This?

EventPulse is a system that:

- Accepts events via a REST API (POST /events)
- Pushes them into an async processing queue (Redis + Celery)
- Processes them in the background and persists results to PostgreSQL
- Exposes metrics to Prometheus, visualised in Grafana
- Scales automatically under load using Kubernetes HPA
- Deploys to AWS via CI/CD pipeline (GitHub Actions)
- Is fully provisioned with Terraform — no manual clicking

This simulates real-world systems like payment processors, analytics ingestion pipelines, and notification services.

---

## Architecture

```
Client
  │
  ▼
Nginx (Reverse Proxy)
  │
  ▼
FastAPI (2+ replicas)
  │              │
  ▼              ▼
PostgreSQL    Redis Queue
                │
                ▼
          Celery Worker (2+ replicas)
                │
                ▼
           PostgreSQL (results)

Monitoring:
FastAPI /metrics ──► Prometheus ──► Grafana
```

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Backend | FastAPI (Python) | Async, fast, production-ready |
| Task Queue | Celery + Redis | Industry-standard async processing |
| Database | PostgreSQL 15 | Production default |
| Reverse Proxy | Nginx | Real reverse proxy experience |
| Containers | Docker (multi-stage) | Lean, secure images |
| Orchestration | Kubernetes (k3s on EC2) | Real K8s without EKS cost |
| Cloud | AWS (EC2, RDS, ECR) | Real cloud environment |
| IaC | Terraform | All infrastructure as code |
| CI/CD | GitHub Actions | Automated test → build → deploy |
| Monitoring | Prometheus + Grafana | Industry-standard observability |
| Load Testing | k6 | Scriptable, modern load testing |

---

## Project Structure

```
eventpulse/
├── app/                    # FastAPI application
│   ├── main.py
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── tasks/              # Celery tasks
│   └── metrics.py          # Prometheus custom metrics
├── worker/                 # Celery worker entry point
├── nginx/                  # Nginx config
├── k8s/                    # Kubernetes manifests
│   ├── deployments/
│   ├── services/
│   ├── configmaps/
│   ├── ingress/
│   ├── hpa/
│   └── monitoring/
├── terraform/              # Infrastructure as Code
│   ├── modules/
│   │   ├── vpc/
│   │   ├── ec2/
│   │   ├── rds/
│   │   └── ecr/
│   └── main.tf
├── .github/
│   └── workflows/
│       ├── ci.yml          # Test on PR
│       └── deploy.yml      # Build + deploy on push to main
├── scripts/
│   └── load-test.js        # k6 load test script
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   ├── kubernetes.md
│   ├── terraform.md
│   └── chaos-testing.md
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Local Development

### Prerequisites
- Docker + Docker Compose
- Python 3.11+
- Poetry

### Run locally
```bash
docker compose up -d
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"type": "user.signup", "source": "web", "payload": {"user_id": "123"}}'
```

---

## Kubernetes Deployment (local)

```bash
# Start Minikube
minikube start

# Apply all manifests
kubectl apply -f k8s/

# Check pods
kubectl get pods

# Access API
minikube service fastapi-service --url
```

See [docs/kubernetes.md](docs/kubernetes.md) for full instructions.

---

## AWS Deployment

```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

See [docs/terraform.md](docs/terraform.md) for full instructions.

---

## Monitoring

- Prometheus: `http://<node-ip>:9090`
- Grafana: `http://<node-ip>:3000` (admin / admin)

Dashboard includes: request rate, P95 latency, error rate, events processed/min, pod CPU/memory.

SLO: 99% of requests complete under 300ms.

---

## Chaos Testing

See [docs/chaos-testing.md](docs/chaos-testing.md) for documented scenarios:

1. Spike load → HPA pod scaling
2. Pod kill mid-load → zero-downtime recovery
3. DB outage → graceful error handling
4. CPU stress → resource limit behaviour
5. Normal load baseline

---

## CI/CD Pipeline

| Event | Action |
|---|---|
| PR to `develop` | Run tests |
| Push to `develop` | Deploy to staging namespace |
| Push to `main` | Build image → push to ECR → deploy to production |

---

## Contributing (Team Workflow)

Each task has a corresponding GitHub Issue with a role label:

| Label | Role |
|---|---|
| `backend` | Backend Engineer |
| `devops` | DevOps Engineer |
| `infrastructure` | Infrastructure Engineer |
| `sre` | SRE / Observability |
| `docs` | Documentation |

Branch naming: `feature/<label>-<short-description>`
Example: `feature/backend-fastapi-setup`

1. Pick an issue from the Project board
2. Create a branch: `git checkout -b feature/backend-fastapi-setup`
3. Work, commit with conventional commits: `feat(backend): set up FastAPI structure`
4. Open PR → closes issue automatically on merge
5. Merge to `develop` → CI runs

---

## Author

Mark Kungu — Built as a full-stack DevOps learning project covering backend engineering, containerisation, Kubernetes, cloud infrastructure, CI/CD, and observability.
