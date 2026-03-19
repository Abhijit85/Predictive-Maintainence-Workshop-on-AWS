resource "mongodbatlas_privatelink_endpoint" "atlas" {
  count         = var.atlas_create && var.aws_create ? 1 : 0
  project_id    = mongodbatlas_project.project[0].id
  provider_name = "AWS"
  region        = data.aws_region.current.id
}

resource "aws_vpc_endpoint" "atlas" {
  count              = var.atlas_create && var.aws_create ? 1 : 0
  vpc_id             = module.vpc[0].vpc_id
  service_name       = mongodbatlas_privatelink_endpoint.atlas[0].endpoint_service_name
  vpc_endpoint_type  = "Interface"
  subnet_ids         = module.vpc[0].private_subnets
  security_group_ids = [aws_security_group.privatelink[0].id]

  tags = {
    Name = "${var.aws_app_name}-atlas-privatelink"
  }
}

resource "mongodbatlas_privatelink_endpoint_service" "atlas" {
  count               = var.atlas_create && var.aws_create ? 1 : 0
  project_id          = mongodbatlas_project.project[0].id
  private_link_id     = mongodbatlas_privatelink_endpoint.atlas[0].private_link_id
  endpoint_service_id = aws_vpc_endpoint.atlas[0].id
  provider_name       = "AWS"
}

resource "aws_security_group" "privatelink" {
  count       = var.atlas_create && var.aws_create ? 1 : 0
  name        = "${var.aws_app_name}-privatelink-sg"
  description = "Security group for MongoDB Atlas PrivateLink"
  vpc_id      = module.vpc[0].vpc_id

  ingress {
    description = "MongoDB from VPC"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = [module.vpc[0].vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.aws_app_name}-privatelink-sg"
  }
}
