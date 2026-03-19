locals {
  azs          = formatlist("${data.aws_region.current.region}%s", var.aws_availability_zones)
  fastapi_port = lookup(var.aws_app_envs, "REACT_APP_FASTAPI_PORT", "5001")

  s3 = "${data.aws_caller_identity.current.account_id}-${var.aws_app_name}"
  atlas_connection_string = var.atlas_create ? replace(mongodbatlas_cluster.cluster[0].connection_strings[0].standard_srv,
    "mongodb+srv://",
  "mongodb+srv://adminuser:${urlencode(var.atlas_password)}@") : var.mongodb_uri

  image = var.app_use_public_ecr ? var.aws_image : "${aws_ecr_repository.ecr_private_repository[0].repository_url}:latest"

  # Secret ARNs for container definitions
  secret_refs = var.aws_create ? [
    {
      name      = "MONGODB_URI"
      valueFrom = "${aws_secretsmanager_secret.app_secrets[0].arn}:MONGODB_URI::"
    },
    {
      name      = "VOYAGE_API_KEY"
      valueFrom = "${aws_secretsmanager_secret.app_secrets[0].arn}:VOYAGE_API_KEY::"
    }
  ] : []

  # CloudWatch log configuration
  log_config = {
    logDriver = "awslogs"
    options = {
      "awslogs-group"         = "/ecs/${var.aws_app_name}"
      "awslogs-region"        = data.aws_region.current.id
      "awslogs-stream-prefix" = "ecs"
    }
  }

  # Base environment variables (shared between API and stream)
  base_envs = merge(
    var.aws_app_envs,
    { BUCKET = local.s3 },
    { INDEXING = var.app_indexing },
    { ENV = "ecs" },
    { GENERATE_MODELS = var.app_generate_models }
  )

  # API-specific environment variables
  api_envs = merge(
    local.base_envs,
    {
      REACT_APP_FASTAPI_HOST = "0.0.0.0"
      REACT_APP_FASTAPI_PORT = local.fastapi_port
    }
  )

  # Stream-specific environment variables
  # Stream runs as a separate ECS task, so it reaches the API via ALB (not localhost)
  stream_envs = merge(
    local.base_envs,
    {
      REACT_APP_FASTAPI_HOST = aws_lb.api[0].dns_name
      REACT_APP_FASTAPI_PORT = "80"
      SNS_ALERT_TOPIC_ARN    = aws_sns_topic.alerts[0].arn
    }
  )

  # API container definition
  api_container = {
    "${var.aws_container_name}-api" = {
      name      = "${var.aws_container_name}-api"
      essential = true
      image     = local.image
      command   = ["python", "fastapi_mcp.py"]

      environment = [for key, value in local.api_envs : { "name" = key, "value" = tostring(value) }]
      secrets     = local.secret_refs

      portMappings = [
        {
          name          = "fastapi-port"
          containerPort = local.fastapi_port
          hostPort      = local.fastapi_port
          protocol      = "tcp"
        }
      ]

      logConfiguration       = local.log_config
      readonlyRootFilesystem = false
    }
  }

  # Stream container definition
  stream_container = {
    "${var.aws_container_name}-stream" = {
      name      = "${var.aws_container_name}-stream"
      essential = true
      image     = local.image
      command   = ["python", "stream.py"]

      environment = [for key, value in local.stream_envs : { "name" = key, "value" = tostring(value) }]
      secrets     = local.secret_refs

      logConfiguration       = local.log_config
      readonlyRootFilesystem = false
    }
  }

  data_files     = fileset("/app_files/data", "**")
  info_files     = fileset("/app_files/info", "**")
  dataset_files  = fileset("/app_files/datasets", "**")
  encoders_files = fileset("/app_files/encoders", "**")
  models_files   = fileset("/app_files/models", "**")

  config_file = fileset("/app_files/config", "config.yaml")
}
