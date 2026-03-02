# =============================================================================
# Application Load Balancer
# =============================================================================
# This file creates the ALB for exposing convoy-api to the internet
# =============================================================================

resource "aws_lb" "convoy" {
  name               = "convoy-alb${var.suffix}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = var.environment == "prod"

  tags = {
    Name        = "convoy-alb${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# Target Group for convoy-api
# =============================================================================

resource "aws_lb_target_group" "convoy_api" {
  name        = "convoy-api-tg${var.suffix}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = {
    Name        = "convoy-api-tg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# ACM Certificate for API Domain
# =============================================================================

resource "aws_acm_certificate" "api" {
  domain_name       = var.api_domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "api-cnvy-ai-cert"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Wait for certificate validation (DNS record must be added manually in Namecheap)
resource "aws_acm_certificate_validation" "api" {
  certificate_arn = aws_acm_certificate.api.arn

  timeouts {
    create = "45m"
  }
}

# =============================================================================
# HTTP Listener (redirects to HTTPS)
# =============================================================================

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.convoy.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = {
    Name        = "convoy-http-listener${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# HTTPS Listener
# =============================================================================

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.convoy.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.api.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.convoy_api.arn
  }

  tags = {
    Name        = "convoy-https-listener${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [aws_acm_certificate_validation.api]
}

# =============================================================================
# Outputs for DNS Configuration
# =============================================================================

output "api_acm_validation_records" {
  description = "DNS records to add in Namecheap for API certificate validation"
  value = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}

output "api_alb_dns_name" {
  description = "ALB DNS name - add CNAME in Namecheap pointing api.cnvy.ai to this"
  value       = aws_lb.convoy.dns_name
}
