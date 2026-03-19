resource "aws_amplify_app" "frontend" {
  count = var.aws_create ? 1 : 0
  name  = "${var.aws_app_name}-ui"

  platform = "WEB"

  # API proxy rules — Amplify proxies /api/* and /health through CloudFront
  # to the ALB. CloudFront is required because Amplify rejects HTTP URLs in
  # proxy rewrite rules (HTTPS only). CloudFront terminates HTTPS and connects
  # to the ALB over HTTP with all caching disabled.
  custom_rule {
    source = "/api/<*>"
    target = "https://${aws_cloudfront_distribution.api_proxy[0].domain_name}/api/<*>"
    status = "200"
  }

  custom_rule {
    source = "/health"
    target = "https://${aws_cloudfront_distribution.api_proxy[0].domain_name}/health"
    status = "200"
  }

  # SPA fallback — must be last
  custom_rule {
    source = "</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>"
    status = "200"
    target = "/index.html"
  }

  tags = {
    Name = "${var.aws_app_name}-ui"
  }
}

resource "aws_amplify_branch" "main" {
  count       = var.aws_create ? 1 : 0
  app_id      = aws_amplify_app.frontend[0].id
  branch_name = "main"
}

output "amplify_app_id" {
  value       = var.aws_create ? aws_amplify_app.frontend[0].id : ""
  description = "Amplify app ID for frontend deployment"
}

output "amplify_app_url" {
  value       = var.aws_create ? "https://main.${aws_amplify_app.frontend[0].default_domain}" : ""
  description = "Amplify frontend URL"
}
