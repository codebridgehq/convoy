# =============================================================================
# ECR Repositories
# =============================================================================
# This file creates ECR repositories for container images:
# - convoy/api: Repository for convoy-api image
# - convoy/worker: Repository for convoy-worker image
# =============================================================================

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
