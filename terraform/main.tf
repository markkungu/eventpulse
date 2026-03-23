module "vpc" {
  source      = "./modules/vpc"
  project     = var.project
  environment = var.environment
}

module "ec2" {
  source            = "./modules/ec2"
  project           = var.project
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_id  = module.vpc.public_subnet_ids[0]
  ec2_sg_id         = module.vpc.ec2_sg_id
  key_name          = var.ec2_key_name
}

module "rds" {
  source              = "./modules/rds"
  project             = var.project
  environment         = var.environment
  private_subnet_ids  = module.vpc.private_subnet_ids
  rds_sg_id           = module.vpc.rds_sg_id
  db_password         = var.db_password
}

module "ecr" {
  source  = "./modules/ecr"
  project = var.project
}
