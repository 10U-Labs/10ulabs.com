resource "aws_iam_role" "ecs_task_role" {
  name = "${var.task_family}-TaskRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.task_family}-TaskRole"
  }
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.task_family}-ExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.task_family}-ExecutionRole"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_ssm_access" {
  name = "SSMParameterAccess"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ]
      Resource = [
        aws_ssm_parameter.github_token.arn
      ]
    }]
  })
}

resource "aws_iam_role" "ec2_runner_role" {
  name = "GitHubSelfHostedRunnerEC2Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  ]

  inline_policy {
    name = "ECRAccess"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect   = "Allow"
        Action   = ["ecr:*"]
        Resource = ["*"]
      }]
    })
  }

  inline_policy {
    name = "SelfTerminate"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect   = "Allow"
        Action   = ["ec2:TerminateInstances"]
        Resource = ["*"]
        Condition = {
          StringEquals = {
            "ec2:ResourceTag/ManagedBy" = "webhook-handler"
          }
        }
      }]
    })
  }

  tags = {
    Name = "GitHubSelfHostedRunnerEC2Role"
  }
}

resource "aws_iam_instance_profile" "ec2_runner" {
  name = "GitHubSelfHostedRunnerInstanceProfile"
  role = aws_iam_role.ec2_runner_role.name

  tags = {
    Name = "GitHubSelfHostedRunnerInstanceProfile"
  }
}

resource "aws_iam_role" "lambda_health_handler" {
  name = "HealthHandler-ServiceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]

  tags = {
    Name = "HealthHandler-ServiceRole"
  }
}

resource "aws_iam_role" "lambda_catchall_handler" {
  name = "CatchAllHandler-ServiceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]

  tags = {
    Name = "CatchAllHandler-ServiceRole"
  }
}

resource "aws_iam_role" "lambda_runners_handler" {
  name = "${var.lambda_function_name}-ServiceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
  ]

  tags = {
    Name = "${var.lambda_function_name}-ServiceRole"
  }
}

resource "aws_iam_role_policy" "lambda_runners_handler_ssm" {
  name = "SSMParameterAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter"]
      Resource = [aws_ssm_parameter.webhook_secret.arn]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_runners_handler_cloudwatch" {
  name = "CloudWatchMetrics"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["cloudwatch:PutMetricData"]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_runners_handler_sqs" {
  name = "SQSAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = [aws_sqs_queue.job_queue.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [aws_sqs_queue.job_queue.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_runners_handler_dynamodb" {
  name = "DynamoDBAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = [
        aws_dynamodb_table.idempotency.arn
      ]
    }]
  })
}

resource "aws_iam_role" "lambda_v1_handler" {
  name = "V1ApiHandler-ServiceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]

  tags = {
    Name = "V1ApiHandler-ServiceRole"
  }
}

resource "aws_iam_role_policy" "lambda_v1_handler_ecs" {
  name = "ECSAccess"
  role = aws_iam_role.lambda_v1_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecs:RunTask",
        "ecs:DescribeTasks",
        "ecs:ListTasks",
        "ecs:StopTask"
      ]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_v1_handler_ec2" {
  name = "EC2Access"
  role = aws_iam_role.lambda_v1_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:CreateTags",
        "ec2:DescribeInstances",
        "ec2:DescribeImages",
        "ec2:DeregisterImage",
        "ec2:DeleteSnapshot",
        "ec2:DescribeSnapshots",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups"
      ]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_v1_handler_iam_pass_role" {
  name = "IAMPassRole"
  role = aws_iam_role.lambda_v1_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["iam:PassRole"]
      Resource = [
        aws_iam_role.ecs_task_role.arn,
        aws_iam_role.ecs_execution_role.arn,
        aws_iam_role.ec2_runner_role.arn
      ]
      Condition = {
        StringEquals = {
          "iam:PassedToService" = [
            "ecs-tasks.amazonaws.com",
            "ec2.amazonaws.com"
          ]
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_v1_handler_ecr" {
  name = "ECRAccess"
  role = aws_iam_role.lambda_v1_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecr:DescribeImages",
        "ecr:ListImages",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchDeleteImage"
      ]
      Resource = [aws_ecr_repository.runner.arn]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_v1_handler_ssm" {
  name = "SSMParameterAccess"
  role = aws_iam_role.lambda_v1_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssm:GetParameter"]
      Resource = [
        "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/github-runner/*"
      ]
    }]
  })
}
