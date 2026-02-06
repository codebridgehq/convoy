# =============================================================================
# Terraform Outputs
# =============================================================================
# This file exports important values from the infrastructure deployment
# =============================================================================

# =============================================================================
# VPC Outputs
# =============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnets
}

# =============================================================================
# RDS Outputs
# =============================================================================

output "convoy_db_endpoint" {
  description = "Endpoint of the Convoy PostgreSQL database"
  value       = aws_db_instance.convoy.endpoint
}

output "temporal_db_endpoint" {
  description = "Endpoint of the Temporal PostgreSQL database"
  value       = aws_db_instance.temporal.endpoint
}

# =============================================================================
# ECR Outputs
# =============================================================================

output "ecr_convoy_api_repository_url" {
  description = "URL of the convoy-api ECR repository"
  value       = aws_ecr_repository.convoy_api.repository_url
}

output "ecr_convoy_worker_repository_url" {
  description = "URL of the convoy-worker ECR repository"
  value       = aws_ecr_repository.convoy_worker.repository_url
}

# =============================================================================
# ECS Outputs
# =============================================================================

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.convoy.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.convoy.arn
}

# =============================================================================
# ALB Outputs
# =============================================================================

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.convoy.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer (for Route53)"
  value       = aws_lb.convoy.zone_id
}

output "api_url" {
  description = "URL to access the convoy-api"
  value       = "http://${aws_lb.convoy.dns_name}"
}

# =============================================================================
# Service Discovery Outputs
# =============================================================================

output "service_discovery_namespace" {
  description = "Service discovery namespace for internal DNS"
  value       = aws_service_discovery_private_dns_namespace.convoy.name
}

output "temporal_internal_address" {
  description = "Internal address for Temporal server"
  value       = "temporal.convoy.local:7233"
}

# =============================================================================
# Secrets Outputs
# =============================================================================

output "convoy_db_secret_arn" {
  description = "ARN of the Convoy database credentials secret"
  value       = aws_secretsmanager_secret.convoy_db.arn
}

output "temporal_db_secret_arn" {
  description = "ARN of the Temporal database credentials secret"
  value       = aws_secretsmanager_secret.temporal_db.arn
}

# =============================================================================
# Deployment Commands
# =============================================================================

output "deployment_commands" {
  description = "Commands to deploy application images"
  value       = <<-EOT
    # Login to ECR
    aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com

    # Build and push convoy-api
    docker build -t ${aws_ecr_repository.convoy_api.repository_url}:latest --target api_prod -f core/Dockerfile.api core/
    docker push ${aws_ecr_repository.convoy_api.repository_url}:latest

    # Build and push convoy-worker
    docker build -t ${aws_ecr_repository.convoy_worker.repository_url}:latest --target worker_prod -f core/Dockerfile.worker core/
    docker push ${aws_ecr_repository.convoy_worker.repository_url}:latest

    # Force new deployment
    aws ecs update-service --cluster ${aws_ecs_cluster.convoy.name} --service convoy-api --force-new-deployment
    aws ecs update-service --cluster ${aws_ecs_cluster.convoy.name} --service convoy-worker --force-new-deployment
  EOT
}

output "migration_command" {
  description = "Command to run database migrations"
  value       = <<-EOT
    aws ecs run-task \
      --cluster ${aws_ecs_cluster.convoy.name} \
      --task-definition convoy-api${var.suffix} \
      --launch-type FARGATE \
      --network-configuration "awsvpcConfiguration={subnets=[${join(",", module.vpc.private_subnets)}],securityGroups=[${aws_security_group.ecs_api.id}],assignPublicIp=DISABLED}" \
      --overrides '{"containerOverrides":[{"name":"convoy-api","command":["uv","run","alembic","upgrade","head"]}]}'
  EOT
}
