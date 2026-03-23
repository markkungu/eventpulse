# EventPulse — Production-Grade Event Processing Platform

[![CI](https://github.com/markkungu/eventpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/markkungu/eventpulse/actions/workflows/ci.yml)

> A containerized, auto-scaling, monitored backend system simulating real production workloads.

---

## What Is This?

EventPulse accepts events via REST API, processes them asynchronously, persists results, and exposes everything to a monitoring stack — all running on Kubernetes, deployed to AWS, and fully automated with CI/CD.

This simulates real-world systems: payment processors, analytics ingestion, notification pipelines.

---

## Architecture

```
Client → Nginx → FastAPI ──► Redis Queue ──► Celery Worker ──► PostgreSQL
                    │
                    └──► /metrics ──► Prometheus ──► Grafana

AWS: VPC → EC2 (k3s) + RDS (PostgreSQL) + ECR (images)
IaC: Terraform | CI/CD: GitHub Actions
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | FastAPI + Python 3.11 |
| Async Queue | Celery + Redis |
| Database | PostgreSQL 15 |
| Proxy | Nginx |
| Containers | Docker (multi-stage, non-root) |
| Orchestration | Kubernetes / k3s |
| Cloud | AWS (EC2, RDS, ECR) |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |
| Load Testing | k6 |

---

## Quick Start

```bash
git clone https://github.com/markkungu/eventpulse.git && cd eventpulse
cp .env.example .env
docker compose up -d

curl -X POST http://localhost/events \
  -H "Content-Type: application/json" \
  -d '{"type":"user.signup","source":"web","payload":{"user_id":"abc"}}'
# → {"event_id":"...","status":"queued"}
```

---

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/events` | Submit event — 202, non-blocking |
| `GET` | `/events/{id}` | Fetch event result |
| `GET` | `/health` | DB + Redis health check |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/docs` | OpenAPI docs |

---

## Documentation

| Doc | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | System design and decisions |
| [docs/setup.md](docs/setup.md) | Local development |
| [docs/kubernetes.md](docs/kubernetes.md) | K8s manifests + kubectl commands |
| [docs/terraform.md](docs/terraform.md) | AWS infrastructure with Terraform |
| [docs/deploy-aws.md](docs/deploy-aws.md) | Step-by-step AWS deployment |
| [docs/cicd.md](docs/cicd.md) | CI/CD pipeline and required secrets |
| [docs/chaos-testing.md](docs/chaos-testing.md) | Chaos scenarios and results |
| [scripts/README.md](scripts/README.md) | k6 load test usage |

---

## CI/CD Pipeline

| Trigger | Action |
|---|---|
| PR to `develop`/`main` | Run pytest (real Postgres + Redis) |
| Push to `develop` | Build → ECR → deploy to staging |
| Push to `main` | Build → ECR → deploy to production |

---

## Chaos Testing

Five scenarios documented in [docs/chaos-testing.md](docs/chaos-testing.md):

1. Spike load → HPA scales pods 2→10
2. Pod kill mid-traffic → zero downtime
3. Database outage → graceful 503, auto-recovery
4. CPU stress → resource limits + HPA
5. Normal baseline → performance benchmarks

---

## Author

Mark Kungu — DevOps learning project covering backend, containers, K8s, AWS, CI/CD, and observability.
