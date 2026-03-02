# =============================================================================
# Documentation Hosting Infrastructure
# =============================================================================
# This file creates the infrastructure for hosting Convoy docs on AWS:
# - S3 bucket for static files
# - CloudFront distribution for CDN
# - ACM certificate for HTTPS
# - IAM role for GitHub Actions deployment
# =============================================================================

# =============================================================================
# Variables
# =============================================================================

variable "docs_domain" {
  description = "Domain name for documentation site"
  type        = string
  default     = "docs.cnvy.ai"
}

variable "github_repo" {
  description = "GitHub repository in format owner/repo"
  type        = string
  default     = "Sonic-Web-Dev/convoy"
}

# =============================================================================
# ACM Certificate (must be in us-east-1 for CloudFront)
# =============================================================================

provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = var.aws_profile
}

resource "aws_acm_certificate" "docs" {
  provider          = aws.us_east_1
  domain_name       = var.docs_domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "docs-cnvy-ai-cert"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Wait for certificate validation (DNS record must be added manually in Namecheap)
# This resource will block until the certificate is validated
resource "aws_acm_certificate_validation" "docs" {
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.docs.arn

  timeouts {
    create = "45m"
  }
}

# =============================================================================
# S3 Bucket for Documentation
# =============================================================================

resource "aws_s3_bucket" "docs" {
  bucket = "convoy-docs${var.suffix}"

  tags = {
    Name        = "convoy-docs${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Block all public access - CloudFront will access via OAC
resource "aws_s3_bucket_public_access_block" "docs" {
  bucket = aws_s3_bucket.docs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for rollback capability
resource "aws_s3_bucket_versioning" "docs" {
  bucket = aws_s3_bucket.docs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Bucket policy allowing CloudFront OAC access
resource "aws_s3_bucket_policy" "docs" {
  bucket = aws_s3_bucket.docs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAC"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.docs.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.docs.arn
          }
        }
      }
    ]
  })
}

# =============================================================================
# CloudFront Distribution
# =============================================================================

# Origin Access Control for secure S3 access
resource "aws_cloudfront_origin_access_control" "docs" {
  name                              = "docs-oac${var.suffix}"
  description                       = "OAC for Convoy docs S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Cache policy for static content
resource "aws_cloudfront_cache_policy" "docs" {
  name        = "convoy-docs-cache-policy${var.suffix}"
  comment     = "Cache policy for Convoy documentation"
  default_ttl = 86400    # 24 hours
  max_ttl     = 31536000 # 1 year
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "docs" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [var.docs_domain]
  price_class         = "PriceClass_100" # US, Canada, Europe
  comment             = "Convoy Documentation CDN"

  origin {
    domain_name              = aws_s3_bucket.docs.bucket_regional_domain_name
    origin_id                = "S3-docs"
    origin_access_control_id = aws_cloudfront_origin_access_control.docs.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-docs"
    cache_policy_id        = aws_cloudfront_cache_policy.docs.id
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  # Handle SPA routing - return 404.html for 404s
  custom_error_response {
    error_code            = 404
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 10
  }

  # Handle 403 (access denied) - common with S3
  custom_error_response {
    error_code            = 403
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 10
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.docs.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name        = "convoy-docs-cdn${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [aws_acm_certificate_validation.docs]
}

# =============================================================================
# IAM Role for GitHub Actions (OIDC)
# =============================================================================

# Use existing OIDC Provider for GitHub Actions (already exists in AWS account)
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# IAM Role for GitHub Actions docs deployment
resource "aws_iam_role" "github_docs_deploy" {
  name = "github-docs-deploy${var.suffix}"

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
    Name        = "github-docs-deploy${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Policy for S3 and CloudFront access
resource "aws_iam_role_policy" "github_docs_deploy" {
  name = "docs-deploy-policy"
  role = aws_iam_role.github_docs_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.docs.arn,
          "${aws_s3_bucket.docs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Resource = aws_cloudfront_distribution.docs.arn
      }
    ]
  })
}

# =============================================================================
# Outputs
# =============================================================================

output "docs_acm_validation_records" {
  description = "DNS records to add in Namecheap for certificate validation"
  value = {
    for dvo in aws_acm_certificate.docs.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}

output "docs_cloudfront_domain" {
  description = "CloudFront domain name - add CNAME in Namecheap pointing docs.cnvy.ai to this"
  value       = aws_cloudfront_distribution.docs.domain_name
}

output "docs_cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = aws_cloudfront_distribution.docs.id
}

output "docs_s3_bucket_name" {
  description = "S3 bucket name for docs deployment"
  value       = aws_s3_bucket.docs.id
}

output "github_docs_deploy_role_arn" {
  description = "IAM Role ARN for GitHub Actions - add as AWS_DEPLOY_ROLE_ARN secret"
  value       = aws_iam_role.github_docs_deploy.arn
}
