# Terraform Guide

## What Terraform Does Here

Terraform provisions all AWS infrastructure in code. Running `terraform apply` creates:

- VPC with public and private subnets
- EC2 instance with k3s auto-installed
- RDS PostgreSQL (managed database)
- ECR repository (Docker image registry)
- S3 bucket for Terraform state
- Security groups, IAM roles, route tables

No manual clicking in the AWS console. Everything is reproducible.

---

## Structure

```
terraform/
├── main.tf              # Root module — calls all child modules
├── variables.tf         # Input variables
├── outputs.tf           # Output values (EC2 IP, RDS endpoint, etc.)
├── versions.tf          # Required providers and Terraform version
├── backend.tf           # S3 remote state config
└── modules/
    ├── vpc/             # VPC, subnets, IGW, route tables
    ├── ec2/             # EC2 instance + k3s user_data script
    ├── rds/             # RDS PostgreSQL
    └── ecr/             # ECR repository
```

---

## Prerequisites

```bash
# Install Terraform
sudo snap install terraform --classic
terraform --version

# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, region (e.g. us-east-1), output format (json)

# Verify AWS access
aws sts get-caller-identity
```

---

## First-Time Setup (Bootstrap State Bucket)

Terraform needs an S3 bucket to store its state file before it can manage anything. Create this manually once:

```bash
aws s3api create-bucket \
  --bucket eventpulse-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket eventpulse-terraform-state \
  --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name eventpulse-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

---

## Deploy Infrastructure

```bash
cd terraform/

# Download providers
terraform init

# Preview what will be created (no changes made)
terraform plan

# Create infrastructure (~5-10 minutes)
terraform apply

# View outputs
terraform output
# ec2_public_ip = "x.x.x.x"
# rds_endpoint  = "eventpulse.xxxx.us-east-1.rds.amazonaws.com"
# ecr_url       = "123456789.dkr.ecr.us-east-1.amazonaws.com/eventpulse"
```

---

## Push Docker Image to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(terraform output -raw ecr_url)

# Build and push
docker build -t eventpulse:latest .
docker tag eventpulse:latest $(terraform output -raw ecr_url):latest
docker push $(terraform output -raw ecr_url):latest
```

---

## Deploy App to K8s on EC2

```bash
# Get EC2 IP from Terraform output
EC2_IP=$(terraform output -raw ec2_public_ip)

# Copy K8s manifests to EC2
scp -r ../k8s/ ubuntu@$EC2_IP:/home/ubuntu/k8s/

# SSH in and apply
ssh ubuntu@$EC2_IP
kubectl apply -f /home/ubuntu/k8s/
kubectl get pods
```

---

## Cost Estimate

Running this stack for the week:

| Resource | Type | Cost/day |
|---|---|---|
| EC2 | t3.medium | ~$0.96 |
| RDS | db.t3.micro | ~$0.48 |
| ECR | Storage + transfer | ~$0.01 |
| S3 | State storage | ~$0.00 |
| **Total** | | **~$1.50/day** |

For a full week: ~**$10 total**.

---

## Destroy Everything (Avoid Ongoing Costs)

```bash
cd terraform/
terraform destroy
```

This removes all resources. Run this at end of project to stop billing.

The S3 state bucket and DynamoDB table can be left (cost is negligible) or deleted manually in AWS console.
