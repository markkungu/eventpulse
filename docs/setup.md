# Local Setup Guide

## Prerequisites

Install these before starting:

| Tool | Version | Install |
|---|---|---|
| Docker | 24+ | https://docs.docker.com/engine/install/ |
| Docker Compose | 2.20+ | Included with Docker Desktop |
| Python | 3.11+ | https://www.python.org/downloads/ |
| Poetry | 1.7+ | `curl -sSL https://install.python-poetry.org \| python3 -` |
| kubectl | 1.28+ | `sudo snap install kubectl --classic` |
| Minikube | 1.32+ | https://minikube.sigs.k8s.io/docs/start/ |
| Terraform | 1.6+ | https://developer.hashicorp.com/terraform/install |
| k6 | 0.49+ | https://k6.io/docs/get-started/installation/ |
| AWS CLI | 2.x | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |

---

## Phase 1: Run Locally with Docker Compose

```bash
# Clone the repo
git clone https://github.com/markkungu/eventpulse.git
cd eventpulse

# Copy environment template
cp .env.example .env
# Edit .env if needed (defaults work out of the box)

# Start all services
docker compose up -d

# Check all services are healthy
docker compose ps

# View logs
docker compose logs -f fastapi
docker compose logs -f celery-worker
```

### Test the API

```bash
# Submit an event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"type": "user.signup", "source": "web", "payload": {"user_id": "abc123"}}'

# Response:
# { "event_id": "uuid-here", "status": "queued" }

# Retrieve the processed event (wait ~1 second for worker)
curl http://localhost:8000/events/<event_id>

# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

### Stop everything

```bash
docker compose down          # stop containers
docker compose down -v       # stop + remove volumes (wipes DB)
```

---

## Phase 2: Run on Kubernetes (Minikube)

```bash
# Start Minikube
minikube start --cpus=4 --memory=4096

# Enable Ingress addon
minikube addons enable ingress

# Point Docker to Minikube's registry (build images inside Minikube)
eval $(minikube docker-env)

# Build the image inside Minikube
docker build -t eventpulse:latest .

# Apply all manifests
kubectl apply -f k8s/

# Watch pods come up
kubectl get pods -w

# Get the Minikube IP
minikube ip

# Test the API
curl http://$(minikube ip)/events \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"type": "test.event", "source": "local", "payload": {}}'
```

See [kubernetes.md](kubernetes.md) for deeper details.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/eventpulse` | PostgreSQL connection |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | Celery results |
| `API_SECRET_KEY` | `change-me-in-production` | App secret |
| `LOG_LEVEL` | `INFO` | Logging level |
| `WORKERS` | `2` | Uvicorn worker count |
