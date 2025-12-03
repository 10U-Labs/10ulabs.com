resource "aws_ecs_cluster" "runner" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(local.common_tags, {
    Name = var.cluster_name
  })
}

resource "aws_ecs_cluster_capacity_providers" "runner" {
  cluster_name = aws_ecs_cluster.runner.name

  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 100
    base              = 0
  }
}

resource "aws_ecs_task_definition" "runner" {
  family                   = var.task_family
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn

  ephemeral_storage {
    size_in_gib = 128
  }

  runtime_platform {
    cpu_architecture        = var.fargate_cpu_architecture
    operating_system_family = var.fargate_operating_system_family
  }

  container_definitions = jsonencode([{
    name      = var.container_name
    image     = "${data.terraform_remote_state.ecr.outputs.repository_url}:latest"
    essential = true

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.runner.name
        "awslogs-region"        = local.aws_region
        "awslogs-stream-prefix" = var.log_stream_prefix
      }
    }

    environment = []
  }])

  tags = merge(local.common_tags, {
    Name = var.task_family
  })

  depends_on = [
    aws_iam_role_policy.ecs_task_cloudwatch_logs,
    aws_iam_role_policy.ecs_execution_ssm_access,
    aws_iam_role_policy.ecs_execution_kms_access,
    aws_iam_role_policy_attachment.ecs_execution_role_policy,
  ]
}

resource "aws_cloudwatch_log_group" "runner" {
  name              = "/ecs/${var.task_family}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.task_family}-logs"
  })
}
