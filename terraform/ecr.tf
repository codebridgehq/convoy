# =============================================================================
# ECR Repositories
# =============================================================================
# This file creates ECR repositories for:
# - convoy/api: Convoy API image
# - convoy/worker: Convoy Worker image
# - temporal/server: Temporal server image (copied from Docker Hub)
# - temporal/admin-tools: Temporal admin tools image (copied from Docker Hub)
# =============================================================================

# Note: data.aws_caller_identity.current is defined in main.tf

# Local values for ECR image URLs
locals {
  ecr_prefix = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"

  # Temporal images from our ECR (must be pushed manually or via CI/CD)
  temporal_server_image      = "${local.ecr_prefix}/temporal/server:${var.temporal_version}"
  temporal_admin_tools_image = "${local.ecr_prefix}/temporal/admin-tools:${var.temporal_admin_tools_version}"
  temporal_ui_image          = "${local.ecr_prefix}/temporal/ui:${var.temporal_ui_version}"
}

# =============================================================================
# ECR Repository - temporal/server
# =============================================================================
# Stores the Temporal server image (copied from Docker Hub)

resource "aws_ecr_repository" "temporal_server" {
  name                 = "temporal/server"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "temporal-server-ecr${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecr_lifecycle_policy" "temporal_server" {
  repository = aws_ecr_repository.temporal_server.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# ECR Repository - temporal/admin-tools
# =============================================================================
# Stores the Temporal admin-tools image (copied from Docker Hub)

resource "aws_ecr_repository" "temporal_admin_tools" {
  name                 = "temporal/admin-tools"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "temporal-admin-tools-ecr${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecr_lifecycle_policy" "temporal_admin_tools" {
  repository = aws_ecr_repository.temporal_admin_tools.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# ECR Repository - convoy-api
# =============================================================================

resource "aws_ecr_repository" "convoy_api" {
  name                 = "convoy/api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "convoy-api-ecr${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecr_lifecycle_policy" "convoy_api" {
  repository = aws_ecr_repository.convoy_api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# ECR Repository - convoy-worker
# =============================================================================

resource "aws_ecr_repository" "convoy_worker" {
  name                 = "convoy/worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "convoy-worker-ecr${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecr_lifecycle_policy" "convoy_worker" {
  repository = aws_ecr_repository.convoy_worker.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# ECR Repository - convoy-web
# =============================================================================

resource "aws_ecr_repository" "convoy_web" {
  name                 = "convoy/web"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "convoy-web-ecr${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecr_lifecycle_policy" "convoy_web" {
  repository = aws_ecr_repository.convoy_web.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
