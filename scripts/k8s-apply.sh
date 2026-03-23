#!/bin/bash
# Apply all K8s manifests in the correct order.
# Usage: bash scripts/k8s-apply.sh [namespace]
set -e

NS=${1:-default}
K="kubectl -n $NS"

echo "Deploying EventPulse to namespace: $NS"

# Create namespace if not default
if [ "$NS" != "default" ]; then
  kubectl create namespace "$NS" --dry-run=client -o yaml | kubectl apply -f -
fi

# Order matters: ConfigMap + Secrets first, then Deployments, then Services
$K apply -f k8s/configmaps/
echo "✓ ConfigMaps"

echo ""
echo "⚠  Create secrets manually if not done:"
echo "   kubectl create secret generic app-secrets \\"
echo "     --from-literal=DATABASE_URL='postgresql+asyncpg://...' \\"
echo "     --from-literal=API_SECRET_KEY='...' \\"
echo "     -n $NS"
echo ""

$K apply -f k8s/deployments/
echo "✓ Deployments"

$K apply -f k8s/services/
echo "✓ Services"

$K apply -f k8s/ingress/
echo "✓ Ingress"

$K apply -f k8s/hpa/
echo "✓ HPAs"

$K apply -f k8s/monitoring/
echo "✓ Monitoring (Prometheus + Grafana)"

echo ""
echo "=== Waiting for pods to be ready ==="
$K rollout status deployment/fastapi --timeout=120s
$K rollout status deployment/celery-worker --timeout=120s

echo ""
echo "=== All deployments ready ==="
$K get pods
