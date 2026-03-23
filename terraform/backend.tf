terraform {
  backend "s3" {
    bucket         = "eventpulse-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "eventpulse-terraform-locks"
    encrypt        = true
  }
}
