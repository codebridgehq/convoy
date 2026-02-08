# =============================================================================
# ECS Temporal Services
# =============================================================================
# This file creates:
# 1. temporal-schema-setup: One-time task to initialize DB schema
# 2. temporal: The main Temporal server service
# 3. temporal-create-namespace: One-time task to create default namespace
# =============================================================================

# =============================================================================
# Schema Setup Task Definition (runs once before temporal server)
# =============================================================================
# This task initializes the PostgreSQL database schema required by Temporal.
# It should be run once before starting the Temporal server for the first time.

resource "aws_ecs_task_definition" "temporal_schema_setup" {
  family                   = "temporal-schema-setup${var.suffix}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.temporal_task.arn

  container_definitions = jsonencode([
    {
      name  = "temporal-schema-setup"
      image = local.temporal_admin_tools_image

      entryPoint = ["/bin/sh", "-c"]
      command = [<<-EOT
        set -eu
        echo 'Starting PostgreSQL schema setup...'
        
        # Wait for PostgreSQL to be available
        echo 'Waiting for PostgreSQL to be available...'
        until nc -z -w 5 ${aws_db_instance.temporal.address} 5432; do
          echo 'PostgreSQL not ready, waiting...'
          sleep 2
        done
        echo 'PostgreSQL is available'
        
        # Create and setup temporal database
        echo 'Creating temporal database...'
        temporal-sql-tool --plugin postgres12 --ep ${aws_db_instance.temporal.address} -u temporal -p 5432 --db temporal --tls --tls-disable-host-verification create || echo 'Database may already exist, continuing...'
        
        echo 'Setting up temporal schema...'
        temporal-sql-tool --plugin postgres12 --ep ${aws_db_instance.temporal.address} -u temporal -p 5432 --db temporal --tls --tls-disable-host-verification setup-schema -v 0.0
        
        echo 'Updating temporal schema...'
        temporal-sql-tool --plugin postgres12 --ep ${aws_db_instance.temporal.address} -u temporal -p 5432 --db temporal --tls --tls-disable-host-verification update-schema -d /etc/temporal/schema/postgresql/v12/temporal/versioned
        
        # Create and setup visibility database
        echo 'Creating temporal_visibility database...'
        temporal-sql-tool --plugin postgres12 --ep ${aws_db_instance.temporal.address} -u temporal -p 5432 --db temporal_visibility --tls --tls-disable-host-verification create || echo 'Database may already exist, continuing...'
        
        echo 'Setting up visibility schema...'
        temporal-sql-tool --plugin postgres12 --ep ${aws_db_instance.temporal.address} -u temporal -p 5432 --db temporal_visibility --tls --tls-disable-host-verification setup-schema -v 0.0
        
        echo 'Updating visibility schema...'
        temporal-sql-tool --plugin postgres12 --ep ${aws_db_instance.temporal.address} -u temporal -p 5432 --db temporal_visibility --tls --tls-disable-host-verification update-schema -d /etc/temporal/schema/postgresql/v12/visibility/versioned
        
        echo 'PostgreSQL schema setup complete!'
      EOT
      ]

      secrets = [
        {
          name      = "SQL_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.temporal_db.arn}:password::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.temporal_schema_setup.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "temporal-schema-setup-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Temporal Server Task Definition
# =============================================================================
# Main Temporal server using the production 'server' image instead of 'auto-setup'

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
      image = local.temporal_server_image

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
        { name = "BIND_ON_IP", value = "0.0.0.0" },
        # Note: DYNAMIC_CONFIG_FILE_PATH removed - not available in Fargate without EFS
        # Temporal will use default dynamic config values
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

      healthCheck = {
        command     = ["CMD-SHELL", "nc -z localhost 7233 || exit 1"]
        interval    = 10
        timeout     = 5
        retries     = 10
        startPeriod = 60
      }

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
# Namespace Creation Task Definition (runs once after temporal server is healthy)
# =============================================================================
# This task creates the default namespace in Temporal.
# It should be run after the Temporal server is healthy.

resource "aws_ecs_task_definition" "temporal_create_namespace" {
  family                   = "temporal-create-namespace${var.suffix}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.temporal_task.arn

  container_definitions = jsonencode([
    {
      name  = "temporal-create-namespace"
      image = local.temporal_admin_tools_image

      entryPoint = ["/bin/sh", "-c"]
      command = [<<-EOT
        set -eu
        NAMESPACE=default
        TEMPORAL_ADDRESS=temporal.convoy.local:7233
        
        echo "Waiting for Temporal server to be available..."
        
        # Wait for Temporal server port
        until nc -z -w 5 temporal.convoy.local 7233; do
          echo 'Temporal server not ready, waiting...'
          sleep 5
        done
        echo 'Temporal server port is available'
        
        # Wait for Temporal server to be healthy
        echo 'Waiting for Temporal server to be healthy...'
        max_attempts=30
        attempt=0
        
        until temporal operator cluster health --address $TEMPORAL_ADDRESS 2>/dev/null; do
          attempt=$((attempt + 1))
          if [ $attempt -ge $max_attempts ]; then
            echo "Temporal server not healthy after $max_attempts attempts"
            exit 1
          fi
          echo "Attempt $attempt/$max_attempts - Temporal not healthy yet, waiting..."
          sleep 10
        done
        
        echo "Temporal server is healthy!"
        echo "Creating namespace '$NAMESPACE'..."
        
        # Create namespace (or skip if it already exists)
        temporal operator namespace describe -n $NAMESPACE --address $TEMPORAL_ADDRESS 2>/dev/null || \
          temporal operator namespace create -n $NAMESPACE --address $TEMPORAL_ADDRESS
        
        echo "Namespace '$NAMESPACE' is ready!"
      EOT
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.temporal_create_namespace.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "temporal-create-namespace-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Temporal Service (long-running)
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
