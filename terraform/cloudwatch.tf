# =============================================================================
# CloudWatch Log Groups
# =============================================================================
# This file creates CloudWatch log groups for ECS services
# =============================================================================

resource "aws_cloudwatch_log_group" "convoy_api" {
  name              = "/ecs/convoy-api${var.suffix}"
  retention_in_days = 30

  tags = {
    Name        = "convoy-api-logs${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_log_group" "convoy_worker" {
  name              = "/ecs/convoy-worker${var.suffix}"
  retention_in_days = 30

  tags = {
    Name        = "convoy-worker-logs${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_log_group" "temporal" {
  name              = "/ecs/temporal${var.suffix}"
  retention_in_days = 30

  tags = {
    Name        = "temporal-logs${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
