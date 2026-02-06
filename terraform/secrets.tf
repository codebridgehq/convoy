# =============================================================================
# Secrets Manager
# =============================================================================
# This file creates secrets for sensitive configuration:
# - Database credentials for Convoy and Temporal
# - Connection strings for ECS tasks
# =============================================================================

# =============================================================================
# Random Passwords
# =============================================================================

resource "random_password" "convoy_db" {
  length  = 32
  special = false # Avoid special chars for easier connection string handling
}

resource "random_password" "temporal_db" {
  length  = 32
  special = false
}

# =============================================================================
# Convoy Database Credentials
# =============================================================================

resource "aws_secretsmanager_secret" "convoy_db" {
  name        = "convoy/db-credentials${var.suffix}"
  description = "Database credentials for Convoy PostgreSQL"

  tags = {
    Name        = "convoy-db-credentials${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "convoy_db" {
  secret_id = aws_secretsmanager_secret.convoy_db.id
  secret_string = jsonencode({
    username          = "convoy"
    password          = random_password.convoy_db.result
    host              = aws_db_instance.convoy.address
    port              = 5432
    dbname            = "convoy"
    connection_string = "postgresql+asyncpg://convoy:${random_password.convoy_db.result}@${aws_db_instance.convoy.address}:5432/convoy"
  })
}

# =============================================================================
# Temporal Database Credentials
# =============================================================================

resource "aws_secretsmanager_secret" "temporal_db" {
  name        = "temporal/db-credentials${var.suffix}"
  description = "Database credentials for Temporal PostgreSQL"

  tags = {
    Name        = "temporal-db-credentials${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "temporal_db" {
  secret_id = aws_secretsmanager_secret.temporal_db.id
  secret_string = jsonencode({
    username = "temporal"
    password = random_password.temporal_db.result
    host     = aws_db_instance.temporal.address
    port     = 5432
    dbname   = "temporal"
  })
}

# =============================================================================
# Temporal Address Secret
# =============================================================================

resource "aws_secretsmanager_secret" "temporal_address" {
  name        = "convoy/temporal-address${var.suffix}"
  description = "Temporal server address for Convoy services"

  tags = {
    Name        = "convoy-temporal-address${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "temporal_address" {
  secret_id = aws_secretsmanager_secret.temporal_address.id
  secret_string = jsonencode({
    address = "temporal.convoy.local:7233"
  })
}
