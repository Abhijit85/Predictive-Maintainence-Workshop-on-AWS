resource "aws_cloudfront_distribution" "api_proxy" {
  count   = var.aws_create ? 1 : 0
  comment = "${var.aws_app_name} API proxy (Amplify -> ALB)"
  enabled = true

  origin {
    domain_name = aws_lb.api[0].dns_name
    origin_id   = "alb-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "alb-origin"
    viewer_protocol_policy = "allow-all"

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      cookies {
        forward = "all"
      }
      headers = ["*"]
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
    compress    = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  price_class = "PriceClass_100"

  tags = {
    Name = "${var.aws_app_name}-api-proxy"
  }
}

output "cloudfront_domain_name" {
  value       = var.aws_create ? aws_cloudfront_distribution.api_proxy[0].domain_name : ""
  description = "CloudFront distribution domain name for API proxy"
}
