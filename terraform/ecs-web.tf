# =============================================================================
# ECS convoy-web Service
# =============================================================================
# This file creates the ECS task definition and service for convoy-web
# (Next.js web application)
# =============================================================================

# =============================================================================
# CloudWatch Log Group
# =============================================================================

resource "aws_cloudwatch_log_group" "convoy_web" {
  name              = "/ecs/convoy-web${var.suffix}"
  retention_in_days = 30

  tags = {
    Name        = "convoy-web-logs${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Task Definition
# =============================================================================

resource "aws_ecs_task_definition" "convoy_web" {
  family                   = "convoy-web${var.suffix}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.web_cpu
  memory                   = var.web_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name  = "convoy-web"
      image = "${aws_ecr_repository.convoy_web.repository_url}:latest"

      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "NODE_ENV", value = "production" },
        { name = "HOSTNAME", value = "0.0.0.0" },
        { name = "PORT", value = "3000" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.convoy_web.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "convoy-web-task${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Security Group for Web Service
# =============================================================================

resource "aws_security_group" "ecs_web" {
  name        = "convoy-web-sg${var.suffix}"
  description = "Security group for convoy-web ECS service"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Allow traffic from ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "convoy-web-sg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service
# =============================================================================

resource "aws_ecs_service" "convoy_web" {
  name            = "convoy-web"
  cluster         = aws_ecs_cluster.convoy.id
  task_definition = aws_ecs_task_definition.convoy_web.arn
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_web.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.convoy_web.arn
    container_name   = "convoy-web"
    container_port   = 3000
  }

  # Ensure ALB listener rules are created before the service
  depends_on = [
    aws_lb_listener_rule.web,
    aws_lb_listener_rule.web_www
  ]

  tags = {
    Name        = "convoy-web-service${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# IAM Role for GitHub Actions Web Deployment (OIDC)
# =============================================================================

# IAM Role for GitHub Actions web deployment
resource "aws_iam_role" "github_web_deploy" {
  name = "github-web-deploy${var.suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "github-web-deploy${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Policy for ECR and ECS access
resource "aws_iam_role_policy" "github_web_deploy" {
  name = "web-deploy-policy"
  role = aws_iam_role.github_web_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = aws_ecr_repository.convoy_web.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices"
        ]
        Resource = aws_ecs_service.convoy_web.id
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "ecs:cluster" = aws_ecs_cluster.convoy.arn
          }
        }
      }
    ]
  })
}

# =============================================================================
# Outputs
# =============================================================================

output "github_web_deploy_role_arn" {
  description = "IAM Role ARN for GitHub Actions web deployment - add as WEB_AWS_DEPLOY_ROLE_ARN secret"
  value       = aws_iam_role.github_web_deploy.arn
}

output "convoy_web_ecr_repository_url" {
  description = "ECR repository URL for convoy-web"
  value       = aws_ecr_repository.convoy_web.repository_url
}
