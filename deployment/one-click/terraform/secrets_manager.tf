resource "aws_secretsmanager_secret" "app_secrets" {
  count       = var.aws_create ? 1 : 0
  name        = "${var.aws_app_name}-secrets"
  description = "Secrets for ${var.aws_app_name} application"

  tags = {
    Name = "${var.aws_app_name}-secrets"
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  count     = var.aws_create ? 1 : 0
  secret_id = aws_secretsmanager_secret.app_secrets[0].id

  secret_string = jsonencode({
    MONGODB_URI    = local.atlas_connection_string
    VOYAGE_API_KEY = var.voyage_api_key
  })
}
