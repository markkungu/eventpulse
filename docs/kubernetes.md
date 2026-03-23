# Kubernetes Guide

## Overview

EventPulse runs on Kubernetes. Locally we use Minikube. In production we use k3s installed on an AWS EC2 instance (same K8s API, no EKS cost).

---

## Manifest Structure

```
k8s/
├── deployments/
│   ├── fastapi.yaml        # FastAPI app (replicas: 2)
│   ├── celery-worker.yaml  # Celery worker (replicas: 2)
│   └── redis.yaml          # Redis (replicas: 1)
├── services/
│   ├── fastapi.yaml        # LoadBalancer / NodePort
│   ├── celery-worker.yaml  # ClusterIP (internal only)
│   └── redis.yaml          # ClusterIP (internal only)
├── configmaps/
│   └── app-config.yaml     # Non-sensitive env vars
├── secrets/
│   └── example.yaml        # Template — never commit real secrets
├── ingress/
│   └── ingress.yaml        # Routes external traffic to fastapi
├── hpa/
│   ├── fastapi-hpa.yaml    # Scale fastapi 2→10 at 60% CPU
│   └── worker-hpa.yaml     # Scale workers 2→10 at 60% CPU
└── monitoring/
    ├── prometheus.yaml      # Prometheus deployment + config
    └── grafana.yaml         # Grafana deployment
```

---

## Key Concepts Used

### Deployments
Define the desired state: what image to run, how many replicas, resource limits.

```yaml
resources:
  requests:
    cpu: "100m"       # Guaranteed minimum (0.1 CPU core)
    memory: "128Mi"
  limits:
    cpu: "500m"       # Hard ceiling (0.5 CPU core)
    memory: "512Mi"
```

### Probes
K8s checks these to know if a pod is alive and ready to receive traffic.

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10   # Wait 10s before first check
  periodSeconds: 10          # Check every 10s

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

- **Liveness** fails → K8s restarts the pod
- **Readiness** fails → K8s stops sending traffic to that pod (but doesn't restart it)

### HorizontalPodAutoscaler
Automatically adjusts replica count based on CPU usage.

```yaml
minReplicas: 2
maxReplicas: 10
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 60   # Scale up when avg CPU > 60%
```

### ConfigMap vs Secret
- **ConfigMap** — non-sensitive config (log level, service URLs without passwords)
- **Secret** — sensitive data (DB passwords, API keys) — base64 encoded in manifest, decoded at runtime

---

## Useful Commands

```bash
# See all resources
kubectl get all

# Watch pods in real time
kubectl get pods -w

# Describe a pod (shows events, probe failures, etc.)
kubectl describe pod <pod-name>

# View logs
kubectl logs <pod-name>
kubectl logs <pod-name> -f          # follow
kubectl logs <pod-name> --previous  # crashed pod logs

# Execute into a pod
kubectl exec -it <pod-name> -- /bin/bash

# Scale manually
kubectl scale deployment fastapi --replicas=5

# Trigger a rolling restart (e.g. after config change)
kubectl rollout restart deployment fastapi

# Watch rollout progress
kubectl rollout status deployment fastapi

# Force delete a pod (to test self-healing)
kubectl delete pod <pod-name>

# Watch HPA
kubectl get hpa -w

# See resource usage
kubectl top pods
kubectl top nodes
```

---

## Namespaces

```bash
# List namespaces
kubectl get namespaces

# Deploy to staging namespace
kubectl apply -f k8s/ -n staging

# Switch context to staging
kubectl config set-context --current --namespace=staging

# Switch back to default
kubectl config set-context --current --namespace=default
```

---

## Troubleshooting

| Symptom | Command | Common Cause |
|---|---|---|
| Pod stuck in `Pending` | `kubectl describe pod` | Node has no capacity |
| Pod in `CrashLoopBackOff` | `kubectl logs <pod> --previous` | App error on startup |
| Pod in `ImagePullBackOff` | `kubectl describe pod` | Wrong image name or registry auth |
| Readiness probe failing | `kubectl describe pod` | App not ready / wrong port |
| HPA not scaling | `kubectl describe hpa` | Metrics server not installed |
