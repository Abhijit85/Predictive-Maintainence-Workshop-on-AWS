resource "aws_sns_topic" "alerts" {
  count = var.aws_create ? 1 : 0
  name  = "${var.aws_app_name}-alerts"

  tags = {
    Name = "${var.aws_app_name}-alerts"
  }
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.aws_create && var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "sns_topic_arn" {
  value       = var.aws_create ? aws_sns_topic.alerts[0].arn : ""
  description = "ARN of the SNS alerts topic"
}
