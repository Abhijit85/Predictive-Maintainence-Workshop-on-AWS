resource "aws_cloudwatch_event_rule" "simulation" {
  count               = var.aws_create && var.app_simulation ? 1 : 0
  name                = "${var.aws_app_name}-simulation"
  description         = "Trigger simulation task every minute"
  schedule_expression = "rate(1 minute)"

  tags = {
    Name = "${var.aws_app_name}-simulation"
  }
}

resource "aws_cloudwatch_event_target" "simulation_ecs" {
  count     = var.aws_create && var.app_simulation ? 1 : 0
  rule      = aws_cloudwatch_event_rule.simulation[0].name
  target_id = "${var.aws_app_name}-simulation"
  arn       = module.ecs[0].arn
  role_arn  = aws_iam_role.eventbridge_ecs[0].arn

  ecs_target {
    task_count          = 1
    task_definition_arn = module.ecs_api_service[0].task_definition_arn
    launch_type         = "FARGATE"

    network_configuration {
      subnets          = module.vpc[0].public_subnets
      assign_public_ip = true
    }
  }

  input = jsonencode({
    containerOverrides = [
      {
        name    = "${var.aws_container_name}-api"
        command = ["python", "simulation.py"]
      }
    ]
  })
}

resource "aws_iam_role" "eventbridge_ecs" {
  count = var.aws_create && var.app_simulation ? 1 : 0
  name  = "${var.aws_app_name}-eventbridge-ecs"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.aws_app_name}-eventbridge-ecs"
  }
}

resource "aws_iam_role_policy" "eventbridge_ecs" {
  count = var.aws_create && var.app_simulation ? 1 : 0
  name  = "${var.aws_app_name}-eventbridge-ecs-policy"
  role  = aws_iam_role.eventbridge_ecs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "*"
      }
    ]
  })
}
