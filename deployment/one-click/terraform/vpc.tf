module "vpc" {
  count   = var.aws_create ? 1 : 0
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.0.0"
  name    = var.aws_vpc_name
  cidr    = "10.0.0.0/16"

  azs             = local.azs
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]

  # NAT gateway is not needed — ECS services run in public subnets with
  # assign_public_ip = true, so they reach the internet directly.
  # Private subnets are only used for PrivateLink VPC endpoints.
  enable_nat_gateway = false

  enable_dns_support   = true
  enable_dns_hostnames = true


  default_security_group_ingress = [
    {
      from_port       = 0
      to_port         = 0
      protocol        = "-1"
      prefix_list_ids = aws_ec2_managed_prefix_list.allowed_ips[0].id
    }
  ]
  default_security_group_egress = [
    {
      from_port        = 0
      to_port          = 0
      protocol         = "-1"
      cidr_blocks      = "0.0.0.0/0"
      ipv6_cidr_blocks = "::/0"
    }
  ]

}