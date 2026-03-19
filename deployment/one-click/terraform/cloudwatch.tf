resource "aws_cloudwatch_log_group" "ecs" {
  count             = var.aws_create ? 1 : 0
  name              = "/ecs/${var.aws_app_name}"
  retention_in_days = 30

  tags = {
    Name = "${var.aws_app_name}-logs"
  }
}
