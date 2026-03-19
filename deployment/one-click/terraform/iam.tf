resource "aws_iam_policy" "service_policy" {
  count = var.aws_create ? 1 : 0
  name  = "${var.aws_cluster_name}-Policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Action" : [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:AbortMultipartUpload"
        ],
        "Effect" : "Allow",
        "Resource" : [
          "arn:aws:s3:::${local.s3}",
          "arn:aws:s3:::${local.s3}/*"
        ]
      },
      {
        "Action" : [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel",
          "bedrock:ApplyGuardrail"
        ],
        "Effect" : "Allow",
        "Resource" : "*"
      },
      {
        "Action" : [
          "ecs:DescribeTasks",
          "ecs:ListTasks",
          "ec2:DescribeNetworkInterfaces"
        ],
        "Effect" : "Allow",
        "Resource" : "*"
      },
      {
        "Action" : [
          "secretsmanager:GetSecretValue"
        ],
        "Effect" : "Allow",
        "Resource" : var.aws_create ? aws_secretsmanager_secret.app_secrets[0].arn : "*"
      },
      {
        "Action" : [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Effect" : "Allow",
        "Resource" : "*"
      },
      {
        "Action" : [
          "sns:Publish"
        ],
        "Effect" : "Allow",
        "Resource" : var.aws_create ? aws_sns_topic.alerts[0].arn : "*"
      },
    ]
  })
}
