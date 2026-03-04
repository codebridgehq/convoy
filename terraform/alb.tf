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
# ACM Certificate for Web Domain (cnvy.ai and www.cnvy.ai)
# =============================================================================

resource "aws_acm_certificate" "web" {
  domain_name               = var.web_domain
  subject_alternative_names = ["www.${var.web_domain}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "web-cnvy-ai-cert"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Wait for certificate validation (DNS records must be added manually in Namecheap)
resource "aws_acm_certificate_validation" "web" {
  certificate_arn = aws_acm_certificate.web.arn

  timeouts {
    create = "45m"
  }
}

# =============================================================================
# Target Group for convoy-web
# =============================================================================

resource "aws_lb_target_group" "convoy_web" {
  name        = "convoy-web-tg${var.suffix}"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = {
    Name        = "convoy-web-tg${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
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

  # Default action returns 404 - all traffic should match a host-based rule
  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }

  tags = {
    Name        = "convoy-https-listener${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [aws_acm_certificate_validation.api]
}

# Add web certificate to HTTPS listener
resource "aws_lb_listener_certificate" "web" {
  listener_arn    = aws_lb_listener.https.arn
  certificate_arn = aws_acm_certificate.web.arn

  depends_on = [aws_acm_certificate_validation.web]
}

# =============================================================================
# Host-Based Routing Rules
# =============================================================================

# Route api.cnvy.ai to convoy-api
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.convoy_api.arn
  }

  condition {
    host_header {
      values = [var.api_domain]
    }
  }

  tags = {
    Name        = "convoy-api-rule${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Route cnvy.ai to convoy-web
resource "aws_lb_listener_rule" "web" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.convoy_web.arn
  }

  condition {
    host_header {
      values = [var.web_domain]
    }
  }

  tags = {
    Name        = "convoy-web-rule${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Route www.cnvy.ai to convoy-web
resource "aws_lb_listener_rule" "web_www" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 201

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.convoy_web.arn
  }

  condition {
    host_header {
      values = ["www.${var.web_domain}"]
    }
  }

  tags = {
    Name        = "convoy-web-www-rule${var.suffix}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
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

output "web_acm_validation_records" {
  description = "DNS records to add in Namecheap for Web certificate validation (cnvy.ai and www.cnvy.ai)"
  value = {
    for dvo in aws_acm_certificate.web.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}
