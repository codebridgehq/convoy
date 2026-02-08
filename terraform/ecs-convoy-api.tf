# =============================================================================
# ECS convoy-api Service
# =============================================================================
# This file creates the ECS task definition and service for convoy-api
# =============================================================================

# =============================================================================
# Task Definition
# =============================================================================

resource "aws_ecs_task_definition" "convoy_api" {
  family                   = "convoy-api${var.suffix}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.convoy_api_task.arn

  container_definitions = jsonencode([
    {
      name  = "convoy-api"
      image = "${aws_ecr_repository.convoy_api.repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "DATABASE_ECHO", value = "false" },
        { name = "BATCH_SIZE_THRESHOLD", value = tostring(var.batch_size_threshold) },
        { name = "BATCH_TIME_THRESHOLD_SECONDS", value = tostring(var.batch_time_threshold_seconds) },
        { name = "RESULT_RETENTION_DAYS", value = tostring(var.result_retention_days) },
        { name = "CALLBACK_MAX_RETRIES", value = tostring(var.callback_max_retries) },
        { name = "TEMPORAL_ADDRESS", value = "temporal.convoy.local:7233" },
        { name = "TEMPORAL_NAMESPACE", value = "default" },
        { name = "TEMPORAL_TASK_QUEUE", value = "convoy-tasks" }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.convoy_db.arn}:connection_string::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.convoy_api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "convoy-api-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service
# =============================================================================

resource "aws_ecs_service" "convoy_api" {
  name            = "convoy-api"
  cluster         = aws_ecs_cluster.convoy.id
  task_definition = aws_ecs_task_definition.convoy_api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  # Enable ECS Exec for SSM Session Manager access (used for DB port forwarding)
  enable_execute_command = true

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_api.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.convoy_api.arn
    container_name   = "convoy-api"
    container_port   = 8000
  }

  service_registries {
    registry_arn = aws_service_discovery_service.convoy_api.arn
  }

  # Ensure ALB listener is created before the service
  depends_on = [aws_lb_listener.http]

  tags = {
    Name        = "convoy-api-service${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service Discovery
# =============================================================================

resource "aws_service_discovery_service" "convoy_api" {
  name = "convoy-api"

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
    Name        = "convoy-api-discovery${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
