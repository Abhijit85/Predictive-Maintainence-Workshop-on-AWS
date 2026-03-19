module "ecs_stream_service" {
  count       = var.aws_create ? 1 : 0
  source      = "terraform-aws-modules/ecs/aws//modules/service"
  version     = "6.2.2"
  name        = "${var.aws_cluster_name}-Stream"
  cluster_arn = module.ecs[0].arn

  enable_execute_command = true

  tasks_iam_role_policies = {
    "cluster" : aws_iam_policy.service_policy[0].arn,
  }

  task_exec_iam_role_policies = {
    "cluster" : aws_iam_policy.service_policy[0].arn,
  }

  container_definitions = local.stream_container

  subnet_ids       = module.vpc[0].public_subnets
  assign_public_ip = true

  security_group_egress_rules = {
    egress_all = {
      ip_protocol = "-1"
      cidr_ipv4   = "0.0.0.0/0"
    }
  }

  ephemeral_storage = {
    size_in_gib = 50
  }

  desired_count      = 1
  enable_autoscaling = false
}
