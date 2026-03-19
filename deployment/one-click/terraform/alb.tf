resource "aws_lb" "api" {
  count              = var.aws_create ? 1 : 0
  name               = "${var.aws_app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id, aws_security_group.alb_amplify[0].id]
  subnets            = module.vpc[0].public_subnets

  tags = {
    Name = "${var.aws_app_name}-alb"
  }
}

resource "aws_lb_target_group" "api" {
  count       = var.aws_create ? 1 : 0
  name        = "${var.aws_app_name}-tg"
  port        = local.fastapi_port
  protocol    = "HTTP"
  vpc_id      = module.vpc[0].vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name = "${var.aws_app_name}-tg"
  }
}

resource "aws_lb_listener" "http" {
  count             = var.aws_create ? 1 : 0
  load_balancer_arn = aws_lb.api[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api[0].arn
  }
}

resource "aws_lb_listener" "https" {
  count             = var.aws_create && var.acm_certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.api[0].arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api[0].arn
  }
}

resource "aws_ec2_managed_prefix_list" "allowed_ips" {
  count          = var.aws_create ? 1 : 0
  name           = "${var.aws_app_name}-allowed-ips"
  address_family = "IPv4"
  max_entries    = 40

  dynamic "entry" {
    for_each = var.aws_allowed_ips
    content {
      cidr = entry.value
    }
  }

  tags = {
    Name = "${var.aws_app_name}-allowed-ips"
  }
}

# AWS-managed prefix list for CloudFront origin-facing IPs.
# Amplify uses CloudFront to proxy API requests to the ALB.
data "aws_ec2_managed_prefix_list" "cloudfront" {
  count = var.aws_create ? 1 : 0
  name  = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_security_group" "alb" {
  count       = var.aws_create ? 1 : 0
  name        = "${var.aws_app_name}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = module.vpc[0].vpc_id

  ingress {
    description     = "HTTP from allowed IPs"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    prefix_list_ids = [aws_ec2_managed_prefix_list.allowed_ips[0].id]
  }

  dynamic "ingress" {
    for_each = var.acm_certificate_arn != "" ? [1] : []
    content {
      description     = "HTTPS from allowed IPs"
      from_port       = 443
      to_port         = 443
      protocol        = "tcp"
      prefix_list_ids = [aws_ec2_managed_prefix_list.allowed_ips[0].id]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.aws_app_name}-alb-sg"
  }
}

# Separate SG for Amplify proxy ingress — Amplify Hosting uses CloudFront
# under the hood, so its server-side proxy requests originate from CloudFront's
# origin-facing IPs. The prefix list has ~45 entries which, combined with the
# allowed_ips prefix list (~32 entries), would exceed the default 60-rule-per-SG limit.
resource "aws_security_group" "alb_amplify" {
  count       = var.aws_create ? 1 : 0
  name        = "${var.aws_app_name}-alb-amp-sg"
  description = "Security group for ALB - Amplify proxy (CloudFront origin-facing IPs)"
  vpc_id      = module.vpc[0].vpc_id

  ingress {
    description     = "HTTP from Amplify proxy (CloudFront origin-facing IPs)"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    prefix_list_ids = [data.aws_ec2_managed_prefix_list.cloudfront[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.aws_app_name}-alb-amp-sg"
  }
}

output "alb_dns_name" {
  value       = var.aws_create ? aws_lb.api[0].dns_name : ""
  description = "DNS name of the Application Load Balancer"
}
