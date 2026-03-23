output "ec2_public_ip" {
  description = "Public IP of the k3s EC2 instance"
  value       = module.ec2.public_ip
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker images"
  value       = module.ecr.repository_url
}
