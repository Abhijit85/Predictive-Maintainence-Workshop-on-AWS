module "ecs" {
  count   = var.aws_create ? 1 : 0
  source  = "terraform-aws-modules/ecs/aws//modules/cluster"
  version = "6.2.2"
  name    = var.aws_cluster_name

  default_capacity_provider_strategy = {
    FARGATE = {
      weight = 50
      base   = 1
    }
    FARGATE_SPOT = {
      weight = 50
    }
  }

  create_task_exec_iam_role      = true
  task_exec_iam_role_name        = "${var.aws_cluster_name}-Role"
  task_exec_iam_role_description = "Execution role required to run ${var.aws_cluster_name} tasks"
}

module "ecs_api_service" {
  count       = var.aws_create ? 1 : 0
  source      = "terraform-aws-modules/ecs/aws//modules/service"
  version     = "6.2.2"
  name        = "${var.aws_cluster_name}-API"
  cluster_arn = module.ecs[0].arn

  enable_execute_command = true

  tasks_iam_role_policies = {
    "cluster" : aws_iam_policy.service_policy[0].arn,
  }

  task_exec_iam_role_policies = {
    "cluster" : aws_iam_policy.service_policy[0].arn,
  }

  container_definitions = local.api_container

  subnet_ids       = module.vpc[0].public_subnets
  assign_public_ip = true

  security_group_ingress_rules = {
    ingress_from_alb = {
      from_port                    = local.fastapi_port
      to_port                      = local.fastapi_port
      ip_protocol                  = "tcp"
      description                  = "FastAPI port from ALB"
      referenced_security_group_id = aws_security_group.alb[0].id
    }
  }

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

  health_check_grace_period_seconds = 60

  load_balancer = {
    service = {
      target_group_arn = aws_lb_target_group.api[0].arn
      container_name   = "${var.aws_container_name}-api"
      container_port   = local.fastapi_port
    }
  }
}
