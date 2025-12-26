resource "aws_ecs_cluster" "runner" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = var.cluster_name
  }
}

resource "aws_ecs_cluster_capacity_providers" "runner" {
  cluster_name = aws_ecs_cluster.runner.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 0
    capacity_provider = "FARGATE_SPOT"
    weight            = 100
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

  volume {
    name = "runner-diag"
  }

  container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = "${data.terraform_remote_state.api_shared_docker_repository.outputs.ecr_repository_url}:latest"
      essential = true

      mountPoints = [
        {
          sourceVolume  = "runner-diag"
          containerPath = "/home/runner/_diag"
          readOnly      = false
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_runner.name
          "awslogs-region"        = module.shared.aws_region
          "awslogs-stream-prefix" = var.log_stream_prefix
        }
      }

      environment = []
    },

    {
      name      = "cloudwatch-agent"
      image     = "public.ecr.aws/cloudwatch-agent/cloudwatch-agent:latest"
      essential = false

      mountPoints = [
        {
          sourceVolume  = "runner-diag"
          containerPath = "/home/runner/_diag"
          readOnly      = true
        }
      ]

      environment = [
        {
          name  = "CW_CONFIG_CONTENT"
          value = file("${path.module}/../image_for_ecs_runners/post/cloudwatch-agent-config.json")
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_runner.name
          "awslogs-region"        = module.shared.aws_region
          "awslogs-stream-prefix" = "cloudwatch-agent"
        }
      }
    }
  ])

  tags = {
    Name = var.task_family
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_cloudwatch_logs,
    aws_iam_role_policy.ecs_execution_ssm_access,
    aws_iam_role_policy.ecs_execution_kms_access,
    aws_iam_role_policy_attachment.ecs_execution_role_policy,
  ]
}

resource "aws_cloudwatch_log_group" "ecs_runner" {
  name              = "/ecs/${var.task_family}"
  retention_in_days = 7

  tags = {
    Name = "${var.task_family}Logs"
  }
}
