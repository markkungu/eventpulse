# Architecture

## System Overview

EventPulse is an asynchronous event processing system. Its purpose is to accept high volumes of events, process them reliably in the background, and expose the results via API — while remaining observable, scalable, and resilient.

---

## Component Breakdown

### FastAPI (API Layer)
- Receives `POST /events` — validates payload, pushes to Redis queue, returns event ID immediately
- Receives `GET /events/{id}` — reads processed result from PostgreSQL
- Exposes `GET /health` — used by K8s liveness/readiness probes
- Exposes `GET /metrics` — scraped by Prometheus

Why FastAPI? Async by default, Pydantic validation built-in, automatic OpenAPI docs, production-ready performance.

### Redis (Queue)
- Acts as the message broker between FastAPI and Celery
- Events are pushed as JSON tasks into a named queue
- In-memory — very fast for queue operations
- Not used for permanent storage

### Celery Worker (Processing Layer)
- Pulls tasks from the Redis queue
- Simulates processing (e.g., enrichment, validation, downstream calls)
- Writes final result to PostgreSQL
- Runs as separate pods from FastAPI — can scale independently

Why Celery? Industry standard for Python async task processing. Works natively with Redis and PostgreSQL.

### PostgreSQL (Persistence)
- Stores processed events with status, result, timestamps
- Source of truth for `GET /events/{id}`
- In AWS: replaced by RDS (managed, backups, multi-AZ)

### Nginx (Reverse Proxy)
- Sits in front of FastAPI
- Handles TLS termination (production)
- Rate limiting headers
- Serves as the single entry point

### Prometheus (Metrics Collection)
- Scrapes `/metrics` from all FastAPI pods every 15s
- Stores time-series data
- Evaluates alerting rules

### Grafana (Visualisation)
- Connects to Prometheus as a datasource
- Displays the operational dashboard
- Sends alerts when SLO is breached

---

## Data Flow

```
1. Client sends POST /events
2. FastAPI validates request with Pydantic
3. FastAPI pushes task to Redis queue → returns { event_id, status: "queued" }
4. Celery worker picks up task from queue
5. Worker processes event (transform, enrich, validate)
6. Worker writes result to PostgreSQL → status: "processed"
7. Client polls GET /events/{id} → receives processed result
```

---

## Kubernetes Architecture

```
                    ┌─────────────────────────┐
                    │   Ingress (Nginx)        │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────▼───────────────────┐
              │         fastapi Service               │
              └──────┬───────────────────┬───────────┘
                     │                   │
              ┌──────▼──────┐   ┌────────▼─────────┐
              │  fastapi    │   │    fastapi       │
              │  Pod 1      │   │    Pod 2         │
              └──────┬──────┘   └────────┬─────────┘
                     │                   │
              ┌──────▼───────────────────▼──────────┐
              │         redis Service                │
              └──────────────────┬──────────────────┘
                                 │
              ┌──────────────────▼───────────────────┐
              │         celery-worker Pods (2+)       │
              └──────────────────┬───────────────────┘
                                 │
              ┌──────────────────▼───────────────────┐
              │         PostgreSQL / RDS              │
              └──────────────────────────────────────┘
```

HPA watches CPU on fastapi pods and celery-worker pods — scales between 2 and 10 replicas automatically.

---

## AWS Architecture

```
VPC (10.0.0.0/16)
├── Public Subnet A — EC2 (k3s master + worker)
├── Public Subnet B — EC2 (optional additional node)
├── Private Subnet A — RDS PostgreSQL
└── Private Subnet B — RDS standby (multi-AZ)

ECR — Docker image registry
S3 — Terraform state backend
SSM Parameter Store — secrets (DB password, etc.)
```

---

## Key Design Decisions

| Decision | Chosen | Alternative | Reason |
|---|---|---|---|
| K8s distribution | k3s on EC2 | EKS | EKS costs $0.10/hr for control plane alone; k3s is identical K8s API |
| Queue | Redis + Celery | RabbitMQ + Celery | Redis doubles as cache; simpler ops |
| DB in K8s | RDS (managed) | PostgreSQL pod | Pods are ephemeral; DB needs persistence and backups |
| Monitoring | Prometheus + Grafana | Datadog | Open source, self-hosted, industry standard |
| IaC | Terraform | AWS CDK | Cloud-agnostic, most widely used in industry |
