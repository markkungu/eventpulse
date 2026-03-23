# CI/CD Pipeline Guide

## Overview

Two GitHub Actions workflows handle all automation:

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | PR to `develop` or `main` | Run pytest with real Postgres + Redis |
| `deploy.yml` | Push to `develop` | Build → ECR → deploy to staging |
| `deploy.yml` | Push to `main` | Build → ECR → deploy to production |

---

## Required GitHub Secrets

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `ECR_REPOSITORY_NAME` | `eventpulse` (just the name, not the URL) |
| `ECR_REPOSITORY_URL` | Full ECR URL from `terraform output ecr_repository_url` |
| `EC2_HOST` | EC2 public IP from `terraform output ec2_public_ip` |
| `EC2_SSH_KEY` | Private SSH key contents (the .pem file content) |

---

## CI Workflow — What Happens on a PR

1. Spins up real PostgreSQL 15 + Redis 7 as service containers
2. Installs Poetry + project dependencies
3. Runs `pytest --cov=app --cov-fail-under=70`
4. Fails PR if coverage drops below 70% or any test fails
5. Uploads HTML coverage report as artifact

---

## Deploy Workflow — What Happens on Push to main

```
push to main
  → build Docker image
  → tag with commit SHA + latest
  → push both tags to ECR
  → SSH to EC2
  → kubectl set image (rolling update, zero downtime)
  → kubectl rollout status (waits for completion)
  → done in ~3 minutes
```

Rolling update means:
- K8s terminates pods one at a time
- New pod must pass readiness probe before old pod is removed
- Zero downtime if you have replicas: 2+

---

## Environments

Two K8s namespaces:
- `staging` — updated on every push to `develop`
- `default` — updated only on push to `main`

Create staging namespace:
```bash
kubectl create namespace staging
# Then apply all manifests to staging:
kubectl apply -f k8s/ -n staging
```

---

## Monitoring Deploys

```bash
# Watch rolling update
kubectl rollout status deployment/fastapi

# Check rollout history
kubectl rollout history deployment/fastapi

# Rollback if needed
kubectl rollout undo deployment/fastapi
```
