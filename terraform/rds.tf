# =============================================================================
# RDS PostgreSQL Instances
# =============================================================================
# This file creates the PostgreSQL database instances:
# - convoy-postgresql: Application database for Convoy
# - temporal-postgresql: Database for Temporal server
# =============================================================================

# =============================================================================
# DB Subnet Group
# =============================================================================

resource "aws_db_subnet_group" "convoy" {
  name        = "convoy-db-subnet-group${var.suffix}"
  description = "Database subnet group for Convoy RDS instances"
  subnet_ids  = module.vpc.private_subnets

  tags = {
    Name        = "convoy-db-subnet-group${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# RDS Instance - Convoy PostgreSQL
# =============================================================================

resource "aws_db_instance" "convoy" {
  identifier = "convoy-postgresql${var.suffix}"

  # Engine configuration
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = var.rds_instance_class
  allocated_storage    = 20
  max_allocated_storage = 100 # Enable storage autoscaling up to 100GB

  # Database configuration
  db_name  = "convoy"
  username = "convoy"
  password = random_password.convoy_db.result

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.convoy.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Backup and maintenance
  backup_retention_period = var.environment == "prod" ? 7 : 1
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # High availability (only for prod)
  multi_az = var.environment == "prod"

  # Performance Insights (free tier available)
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Deletion protection
  deletion_protection = var.environment == "prod"
  skip_final_snapshot = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "convoy-postgresql-final-snapshot${var.suffix}" : null

  # Storage
  storage_type      = "gp3"
  storage_encrypted = true

  tags = {
    Name        = "convoy-postgresql${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# RDS Instance - Temporal PostgreSQL
# =============================================================================

resource "aws_db_instance" "temporal" {
  identifier = "temporal-postgresql${var.suffix}"

  # Engine configuration
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = var.rds_instance_class
  allocated_storage    = 20
  max_allocated_storage = 100 # Enable storage autoscaling up to 100GB

  # Database configuration
  db_name  = "temporal"
  username = "temporal"
  password = random_password.temporal_db.result

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.convoy.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Backup and maintenance
  backup_retention_period = var.environment == "prod" ? 7 : 1
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # High availability (only for prod)
  multi_az = var.environment == "prod"

  # Performance Insights (free tier available)
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Deletion protection
  deletion_protection = var.environment == "prod"
  skip_final_snapshot = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "temporal-postgresql-final-snapshot${var.suffix}" : null

  # Storage
  storage_type      = "gp3"
  storage_encrypted = true

  tags = {
    Name        = "temporal-postgresql${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
