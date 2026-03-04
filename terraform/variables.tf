variable "aws_region" {
  description = "The AWS region to deploy in"
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "The AWS CLI profile to use"
}

variable "suffix" {
  description = "Suffix for resource names (e.g. -dev, -prod, or empty string for rebase)"
  type        = string
}

# =============================================================================
# Environment Configuration
# =============================================================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# =============================================================================
# VPC Configuration
# =============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# =============================================================================
# RDS Configuration
# =============================================================================

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

# =============================================================================
# ECS - convoy-api Configuration
# =============================================================================

variable "api_cpu" {
  description = "CPU units for convoy-api (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memory for convoy-api in MB"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of convoy-api tasks"
  type        = number
  default     = 1
}

# =============================================================================
# ECS - convoy-worker Configuration
# =============================================================================

variable "worker_cpu" {
  description = "CPU units for convoy-worker"
  type        = number
  default     = 512
}

variable "worker_memory" {
  description = "Memory for convoy-worker in MB"
  type        = number
  default     = 1024
}

variable "worker_desired_count" {
  description = "Desired number of convoy-worker tasks"
  type        = number
  default     = 1
}

# =============================================================================
# ECS - Temporal Configuration
# =============================================================================

variable "temporal_cpu" {
  description = "CPU units for Temporal server"
  type        = number
  default     = 512
}

variable "temporal_memory" {
  description = "Memory for Temporal server in MB"
  type        = number
  default     = 1024
}

variable "temporal_version" {
  description = "Temporal server version"
  type        = string
  default     = "1.29.2"
}

variable "temporal_admin_tools_version" {
  description = "Temporal admin-tools version for schema setup and namespace creation"
  type        = string
  default     = "1.29"
}

variable "temporal_ui_version" {
  description = "Temporal UI version"
  type        = string
  default     = "2.36.2"
}

variable "postgresql_version" {
  description = "PostgreSQL version for RDS and Docker images"
  type        = string
  default     = "16"
}

# =============================================================================
# Application Configuration
# =============================================================================

variable "batch_size_threshold" {
  description = "Batch size threshold for processing"
  type        = number
  default     = 100
}

variable "batch_time_threshold_seconds" {
  description = "Batch time threshold in seconds"
  type        = number
  default     = 3600
}

variable "batch_check_interval_seconds" {
  description = "Batch check interval in seconds"
  type        = number
  default     = 30
}

variable "result_retention_days" {
  description = "Days to retain results"
  type        = number
  default     = 30
}

variable "callback_max_retries" {
  description = "Maximum callback retry attempts"
  type        = number
  default     = 5
}

variable "callback_http_timeout_seconds" {
  description = "Callback HTTP timeout in seconds"
  type        = number
  default     = 30
}

# =============================================================================
# API Domain Configuration
# =============================================================================

variable "api_domain" {
  description = "Domain name for API (e.g., api.cnvy.ai)"
  type        = string
  default     = "api.cnvy.ai"
}

# =============================================================================
# Web Domain Configuration
# =============================================================================

variable "web_domain" {
  description = "Primary domain name for web app (e.g., cnvy.ai)"
  type        = string
  default     = "cnvy.ai"
}

# =============================================================================
# ECS - convoy-web Configuration
# =============================================================================

variable "web_cpu" {
  description = "CPU units for convoy-web (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "web_memory" {
  description = "Memory for convoy-web in MB"
  type        = number
  default     = 1024
}

variable "web_desired_count" {
  description = "Desired number of convoy-web tasks"
  type        = number
  default     = 1
}
