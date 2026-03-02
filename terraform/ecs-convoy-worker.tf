# =============================================================================
# ECS convoy-worker Service
# =============================================================================
# This file creates the ECS task definition and service for convoy-worker
# =============================================================================

# =============================================================================
# Task Definition
# =============================================================================

resource "aws_ecs_task_definition" "convoy_worker" {
  family                   = "convoy-worker${var.suffix}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.convoy_worker_task.arn

  container_definitions = jsonencode([
    {
      name  = "convoy-worker"
      image = "${aws_ecr_repository.convoy_worker.repository_url}:latest"

      environment = [
        { name = "DATABASE_ECHO", value = "false" },
        { name = "BATCH_SIZE_THRESHOLD", value = tostring(var.batch_size_threshold) },
        { name = "BATCH_TIME_THRESHOLD_SECONDS", value = tostring(var.batch_time_threshold_seconds) },
        { name = "BATCH_CHECK_INTERVAL_SECONDS", value = tostring(var.batch_check_interval_seconds) },
        { name = "RESULT_RETENTION_DAYS", value = tostring(var.result_retention_days) },
        { name = "CALLBACK_MAX_RETRIES", value = tostring(var.callback_max_retries) },
        { name = "CALLBACK_HTTP_TIMEOUT_SECONDS", value = tostring(var.callback_http_timeout_seconds) },
        { name = "TEMPORAL_ADDRESS", value = "temporal.convoy.local:7233" },
        { name = "TEMPORAL_NAMESPACE", value = "default" },
        { name = "TEMPORAL_TASK_QUEUE", value = "convoy-tasks" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "BEDROCK_S3_BUCKET", value = aws_s3_bucket.bedrock_batch.id },
        { name = "BEDROCK_ROLE_ARN", value = aws_iam_role.bedrock_batch.arn },
        { name = "BEDROCK_S3_INPUT_PREFIX", value = "batch-inputs" },
        { name = "BEDROCK_S3_OUTPUT_PREFIX", value = "batch-outputs" }
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
          "awslogs-group"         = aws_cloudwatch_log_group.convoy_worker.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "convoy-worker-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service
# =============================================================================

resource "aws_ecs_service" "convoy_worker" {
  name            = "convoy-worker"
  cluster         = aws_ecs_cluster.convoy.id
  task_definition = aws_ecs_task_definition.convoy_worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_worker.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.convoy_worker.arn
  }

  # Wait for Temporal to be available
  depends_on = [aws_ecs_service.temporal]

  tags = {
    Name        = "convoy-worker-service${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service Discovery
# =============================================================================

resource "aws_service_discovery_service" "convoy_worker" {
  name = "convoy-worker"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.convoy.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  tags = {
    Name        = "convoy-worker-discovery${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
