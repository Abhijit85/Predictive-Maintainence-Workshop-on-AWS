module "s3_bucket" {
  count   = var.aws_create ? 1 : 0
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "4.5.0"
  bucket  = local.s3

  object_lock_enabled = true
  versioning = {
    enabled = true
  }

  force_destroy = true
}

resource "aws_s3_object" "data" {
  for_each = var.aws_create ? local.data_files : []

  bucket      = module.s3_bucket[0].s3_bucket_id
  key         = "input/data/${each.value}"
  source      = "/app_files/data/${each.value}"
  source_hash = filebase64sha256("/app_files/data/${each.value}")

  force_destroy = true
}

resource "aws_s3_object" "info" {
  for_each = var.aws_create ? local.info_files : []

  bucket      = module.s3_bucket[0].s3_bucket_id
  key         = "input/info/${each.value}"
  source      = "/app_files/info/${each.value}"
  source_hash = filebase64sha256("/app_files/info/${each.value}")

  force_destroy = true
}

resource "aws_s3_object" "datasets" {
  for_each = var.aws_create ? local.dataset_files : []

  bucket      = module.s3_bucket[0].s3_bucket_id
  key         = "input/datasets/${each.value}"
  source      = "/app_files/datasets/${each.value}"
  source_hash = filebase64sha256("/app_files/datasets/${each.value}")

  force_destroy = true

}

resource "aws_s3_object" "models" {
  for_each = var.aws_create ? local.models_files : []

  bucket      = module.s3_bucket[0].s3_bucket_id
  key         = "input/models/${each.value}"
  source      = "/app_files/models/${each.value}"
  source_hash = filebase64sha256("/app_files/models/${each.value}")

  force_destroy = true

}

resource "aws_s3_object" "encoders" {
  for_each = var.aws_create ? local.encoders_files : []

  bucket      = module.s3_bucket[0].s3_bucket_id
  key         = "input/encoders/${each.value}"
  source      = "/app_files/encoders/${each.value}"
  source_hash = filebase64sha256("/app_files/encoders/${each.value}")

  force_destroy = true

}

resource "aws_s3_object" "config" {
  for_each = var.aws_create ? local.config_file : []

  bucket      = module.s3_bucket[0].s3_bucket_id
  key         = "input/config/${each.value}"
  source      = "/app_files/config/${each.value}"
  source_hash = filebase64sha256("/app_files/config/${each.value}")

  force_destroy = true

}