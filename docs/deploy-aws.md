# AWS Deployment Runbook

This document walks through deploying EventPulse to AWS after Terraform has provisioned the infrastructure.

## Prerequisites

- `terraform apply` completed (see [terraform.md](terraform.md))
- AWS CLI configured with correct credentials
- Docker installed locally
- SSH key added to your agent: `ssh-add ~/.ssh/your-key.pem`

---

## Step 1: Get Infrastructure Outputs

```bash
cd terraform/
terraform output
# ec2_public_ip      = "x.x.x.x"
# rds_endpoint       = "eventpulse.xxxx.us-east-1.rds.amazonaws.com:5432"
# ecr_repository_url = "123456789.dkr.ecr.us-east-1.amazonaws.com/eventpulse"
```

Save these — you'll need them below.

---

## Step 2: Push Docker Image to ECR

```bash
ECR_URL=$(terraform output -raw ecr_repository_url)
AWS_REGION="us-east-1"

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URL

# Build and push
docker build -t eventpulse:latest .
docker tag eventpulse:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

---

## Step 3: Configure K8s Manifests for AWS

```bash
EC2_IP=$(terraform output -raw ec2_public_ip)
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
ECR_URL=$(terraform output -raw ecr_repository_url)

# Update image URL in deployments
sed -i "s|image: eventpulse:latest|image: $ECR_URL:latest|g" k8s/deployments/*.yaml

# Create the DB secret on EC2
ssh ubuntu@$EC2_IP "kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL='postgresql+asyncpg://postgres:YOUR_DB_PASS@$RDS_ENDPOINT/eventpulse' \
  --from-literal=API_SECRET_KEY='$(openssl rand -hex 32)' \
  --dry-run=client -o yaml | kubectl apply -f -"
```

---

## Step 4: Apply K8s Manifests

```bash
# Copy manifests to EC2
scp -r k8s/ ubuntu@$EC2_IP:/home/ubuntu/

# SSH in and apply
ssh ubuntu@$EC2_IP << 'ENDSSH'
  # Run migrations first
  kubectl run migrations --image=ECR_URL:latest --restart=Never \
    --env="DATABASE_URL=postgresql://postgres:pass@rds-endpoint/eventpulse" \
    --command -- python -m alembic upgrade head
  kubectl wait --for=condition=complete --timeout=60s pod/migrations

  # Apply all manifests
  kubectl apply -f /home/ubuntu/k8s/configmaps/
  kubectl apply -f /home/ubuntu/k8s/deployments/
  kubectl apply -f /home/ubuntu/k8s/services/
  kubectl apply -f /home/ubuntu/k8s/ingress/
  kubectl apply -f /home/ubuntu/k8s/hpa/
  kubectl apply -f /home/ubuntu/k8s/monitoring/

  kubectl get pods -w
ENDSSH
```

---

## Step 5: Verify

```bash
EC2_IP=$(terraform output -raw ec2_public_ip)

# Test API
curl http://$EC2_IP/health
curl -X POST http://$EC2_IP/events \
  -H "Content-Type: application/json" \
  -d '{"type": "smoke.test", "source": "deploy", "payload": {}}'
```

Expected: `{"status": "ok"}` from health, `{"event_id": "...", "status": "queued"}` from events.

---

## Teardown

```bash
cd terraform/
terraform destroy
```

All resources destroyed. Verify in AWS console: no running EC2, RDS, NAT gateways.
