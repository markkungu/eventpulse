variable "aws_region" {
  description = "AWS region to deploy infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "eventpulse"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "ec2_key_name" {
  description = "Name of the AWS key pair for SSH access to EC2"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}
