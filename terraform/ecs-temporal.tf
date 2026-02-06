# =============================================================================
# ECS Temporal Service
# =============================================================================
# This file creates the ECS task definition and service for Temporal server
# =============================================================================

# =============================================================================
# Task Definition
# =============================================================================

resource "aws_ecs_task_definition" "temporal" {
  family                   = "temporal${var.suffix}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.temporal_cpu
  memory                   = var.temporal_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.temporal_task.arn

  container_definitions = jsonencode([
    {
      name  = "temporal"
      image = "temporalio/auto-setup:${var.temporal_version}"

      portMappings = [
        {
          containerPort = 7233
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "DB", value = "postgres12" },
        { name = "DB_PORT", value = "5432" },
        { name = "POSTGRES_USER", value = "temporal" },
        { name = "POSTGRES_SEEDS", value = aws_db_instance.temporal.address },
        { name = "DYNAMIC_CONFIG_FILE_PATH", value = "config/dynamicconfig/development-sql.yaml" },
        { name = "TEMPORAL_ADDRESS", value = "temporal.convoy.local:7233" },
        { name = "TEMPORAL_CLI_ADDRESS", value = "temporal.convoy.local:7233" },
        # SSL configuration for RDS PostgreSQL
        { name = "SQL_TLS_ENABLED", value = "true" },
        { name = "SQL_TLS", value = "true" },
        { name = "SQL_TLS_DISABLE_HOST_VERIFICATION", value = "true" }
      ]

      secrets = [
        {
          name      = "POSTGRES_PWD"
          valueFrom = "${aws_secretsmanager_secret.temporal_db.arn}:password::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.temporal.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "temporal-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service
# =============================================================================

resource "aws_ecs_service" "temporal" {
  name            = "temporal"
  cluster         = aws_ecs_cluster.convoy.id
  task_definition = aws_ecs_task_definition.temporal.arn
  desired_count   = 1 # Single instance for Temporal
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_temporal.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.temporal.arn
  }

  # Wait for RDS to be available
  depends_on = [aws_db_instance.temporal]

  tags = {
    Name        = "temporal-service${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service Discovery
# =============================================================================

resource "aws_service_discovery_service" "temporal" {
  name = "temporal"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.convoy.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {}

  tags = {
    Name        = "temporal-discovery${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
