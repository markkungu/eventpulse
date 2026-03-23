#!/bin/bash
# Bootstrap Terraform remote state (run ONCE before terraform init).
# Usage: bash scripts/aws-bootstrap.sh
set -e

REGION=${AWS_REGION:-us-east-1}
BUCKET="eventpulse-terraform-state"
TABLE="eventpulse-terraform-locks"

echo "=== Bootstrapping Terraform remote state ==="
echo "Region: $REGION"

echo "Creating S3 bucket: $BUCKET"
aws s3api create-bucket \
  --bucket "$BUCKET" \
  --region "$REGION" \
  2>/dev/null || echo "Bucket already exists"

aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

echo "Creating DynamoDB table: $TABLE"
aws dynamodb create-table \
  --table-name "$TABLE" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" \
  2>/dev/null || echo "Table already exists"

echo ""
echo "✓ Bootstrap complete. Now run:"
echo "  cd terraform && terraform init"
