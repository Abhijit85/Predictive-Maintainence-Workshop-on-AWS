resource "aws_ecr_repository" "ecr_private_repository" {
  count                = !var.app_use_public_ecr ? 1 : 0
  name                 = var.aws_app_name
  image_tag_mutability = "MUTABLE"

  force_delete = true
}