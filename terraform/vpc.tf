# =============================================================================
# VPC and Networking Infrastructure
# =============================================================================
# This file creates the network foundation for the Convoy ECS deployment:
# - VPC with public and private subnets
# - Internet Gateway for public subnet access
# - NAT Gateway for private subnet outbound access
# - Security groups for ALB, ECS services, and RDS
# =============================================================================

locals {
  vpc_name = "convoy-vpc${var.suffix}"
}

# =============================================================================
# VPC Module
# =============================================================================

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = local.vpc_name
  cidr = var.vpc_cidr

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  # NAT Gateway for private subnet outbound access
  enable_nat_gateway     = true
  single_nat_gateway     = true # Cost optimization - use one NAT gateway
  one_nat_gateway_per_az = false

  # DNS settings required for ECS and Service Discovery
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = local.vpc_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  public_subnet_tags = {
    Type = "public"
  }

  private_subnet_tags = {
    Type = "private"
  }
}

# =============================================================================
# Security Group - Application Load Balancer
# =============================================================================

resource "aws_security_group" "alb" {
  name        = "convoy-alb-sg${var.suffix}"
  description = "Security group for Convoy Application Load Balancer"
  vpc_id      = module.vpc.vpc_id

  # HTTP access from internet
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access from internet
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "convoy-alb-sg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Security Group - ECS convoy-api
# =============================================================================

resource "aws_security_group" "ecs_api" {
  name        = "convoy-ecs-api-sg${var.suffix}"
  description = "Security group for convoy-api ECS service"
  vpc_id      = module.vpc.vpc_id

  # Allow traffic from ALB on port 8000
  ingress {
    description     = "HTTP from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow all outbound traffic (for database, Temporal, etc.)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "convoy-ecs-api-sg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Security Group - ECS convoy-worker
# =============================================================================

resource "aws_security_group" "ecs_worker" {
  name        = "convoy-ecs-worker-sg${var.suffix}"
  description = "Security group for convoy-worker ECS service"
  vpc_id      = module.vpc.vpc_id

  # Worker doesn't need inbound traffic - only outbound
  # Allow all outbound traffic (for database, Temporal, S3, Bedrock, etc.)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "convoy-ecs-worker-sg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Security Group - ECS Temporal
# =============================================================================

resource "aws_security_group" "ecs_temporal" {
  name        = "convoy-ecs-temporal-sg${var.suffix}"
  description = "Security group for Temporal ECS service"
  vpc_id      = module.vpc.vpc_id

  # Allow gRPC traffic from convoy-api and convoy-worker
  ingress {
    description = "gRPC from ECS services"
    from_port   = 7233
    to_port     = 7233
    protocol    = "tcp"
    security_groups = [
      aws_security_group.ecs_api.id,
      aws_security_group.ecs_worker.id
    ]
  }

  # Allow all outbound traffic (for database)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "convoy-ecs-temporal-sg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Security Group - RDS PostgreSQL
# =============================================================================

resource "aws_security_group" "rds" {
  name        = "convoy-rds-sg${var.suffix}"
  description = "Security group for RDS PostgreSQL instances"
  vpc_id      = module.vpc.vpc_id

  # Allow PostgreSQL traffic from ECS services
  ingress {
    description = "PostgreSQL from ECS services"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [
      aws_security_group.ecs_api.id,
      aws_security_group.ecs_worker.id,
      aws_security_group.ecs_temporal.id
    ]
  }

  # No outbound traffic needed for RDS
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "convoy-rds-sg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Service Discovery Namespace
# =============================================================================

resource "aws_service_discovery_private_dns_namespace" "convoy" {
  name        = "convoy.local"
  description = "Private DNS namespace for Convoy services"
  vpc         = module.vpc.vpc_id

  tags = {
    Name        = "convoy-service-discovery${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
