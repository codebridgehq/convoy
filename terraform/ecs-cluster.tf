# =============================================================================
# ECS Cluster
# =============================================================================
# This file creates the ECS Fargate cluster with CloudWatch Container Insights
# =============================================================================

resource "aws_ecs_cluster" "convoy" {
  name = "convoy${var.suffix}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "convoy-ecs-cluster${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecs_cluster_capacity_providers" "convoy" {
  cluster_name = aws_ecs_cluster.convoy.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}
