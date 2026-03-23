resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-rds-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "${var.project}-rds-subnet-group" }
}

resource "aws_db_instance" "postgres" {
  identifier           = "${var.project}-postgres"
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  storage_type         = "gp2"
  db_name              = "eventpulse"
  username             = "postgres"
  password             = var.db_password
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_sg_id]

  backup_retention_period = 7
  skip_final_snapshot     = true
  deletion_protection     = false

  tags = { Name = "${var.project}-postgres", Project = var.project }
}

resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project}/db_password"
  type  = "SecureString"
  value = var.db_password
  tags  = { Project = var.project }
}
