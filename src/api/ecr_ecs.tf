resource "aws_ecr_repository" "runner" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  force_delete = true

  tags = merge(local.common_tags, {
    Name = var.ecr_repository_name
  })
}

resource "aws_ecr_lifecycle_policy" "runner" {
  repository = aws_ecr_repository.runner.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["stable"]
          countType     = "imageCountMoreThan"
          countNumber   = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 10
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 20
        selection = {
          tagStatus   = "any"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      }
    ]
  })
}

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

  capacity_providers = ["FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
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

  runtime_platform {
    cpu_architecture        = var.fargate_cpu_architecture
    operating_system_family = var.fargate_operating_system_family
  }

  container_definitions = jsonencode([{
    name      = var.container_name
    image     = "${aws_ecr_repository.runner.repository_url}:latest"
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
}

resource "aws_cloudwatch_log_group" "runner" {
  name              = "/ecs/${var.task_family}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.task_family}-logs"
  })
}
