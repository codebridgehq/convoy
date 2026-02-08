# =============================================================================
# IAM Roles for ECS
# =============================================================================
# This file creates IAM roles for ECS tasks:
# - Task Execution Role: Used by ECS agent to pull images and access secrets
# - Task Roles: Runtime permissions for each service
# =============================================================================

# =============================================================================
# ECS Task Execution Role
# =============================================================================
# This role is used by the ECS agent to:
# - Pull container images from ECR
# - Send logs to CloudWatch
# - Retrieve secrets from Secrets Manager

resource "aws_iam_role" "ecs_task_execution" {
  name = "convoy-ecs-task-execution${var.suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "convoy-ecs-task-execution${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Attach the AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for Secrets Manager access
resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.convoy_db.arn,
          aws_secretsmanager_secret.temporal_db.arn,
          aws_secretsmanager_secret.temporal_address.arn
        ]
      }
    ]
  })
}

# =============================================================================
# convoy-api Task Role
# =============================================================================
# Runtime permissions for convoy-api service

resource "aws_iam_role" "convoy_api_task" {
  name = "convoy-api-task${var.suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "convoy-api-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# SSM permissions for ECS Exec (enables SSM Session Manager port forwarding to RDS)
resource "aws_iam_role_policy" "convoy_api_ssm" {
  name = "ssm-exec-access"
  role = aws_iam_role.convoy_api_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SSMMessages"
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      }
    ]
  })
}

# =============================================================================
# convoy-worker Task Role
# =============================================================================
# Runtime permissions for convoy-worker service
# Needs access to Bedrock and S3 for batch processing

resource "aws_iam_role" "convoy_worker_task" {
  name = "convoy-worker-task${var.suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "convoy-worker-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Bedrock batch inference permissions
resource "aws_iam_role_policy" "convoy_worker_bedrock" {
  name = "bedrock-access"
  role = aws_iam_role.convoy_worker_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockBatchOperations"
        Effect = "Allow"
        Action = [
          "bedrock:CreateModelInvocationJob",
          "bedrock:GetModelInvocationJob",
          "bedrock:ListModelInvocationJobs",
          "bedrock:StopModelInvocationJob"
        ]
        Resource = "*"
      },
      {
        Sid    = "PassRoleToBedrock"
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = aws_iam_role.bedrock_batch.arn
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "bedrock.amazonaws.com"
          }
        }
      }
    ]
  })
}

# S3 access for batch input/output
resource "aws_iam_role_policy" "convoy_worker_s3" {
  name = "s3-access"
  role = aws_iam_role.convoy_worker_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.bedrock_batch.arn
      },
      {
        Sid    = "S3ReadWriteObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.bedrock_batch.arn}/*"
      }
    ]
  })
}

# =============================================================================
# Temporal Task Role
# =============================================================================
# Runtime permissions for Temporal server

resource "aws_iam_role" "temporal_task" {
  name = "temporal-task${var.suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "temporal-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Temporal doesn't need special AWS permissions - it only talks to its database
