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

  tags = merge(local.common_tags, {
    Name = "${var.task_family}-TaskRole"
  })
}

resource "aws_iam_role_policy" "ecs_task_cloudwatch_logs" {
  name = "CloudWatchLogsAccess"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ]
      Resource = [
        "arn:aws:logs:${local.aws_region}:${local.aws_account_id}:log-group:/github-runner/diag:*"
      ]
    }]
  })
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

  tags = merge(local.common_tags, {
    Name = "${var.task_family}-ExecutionRole"
  })
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
        data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter
      ]
    }]
  })
}

resource "aws_iam_role_policy" "ecs_execution_kms_access" {
  name = "KMSDecrypt"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]
      Resource = ["*"]
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

  tags = merge(local.common_tags, {
    Name = "GitHubSelfHostedRunnerEC2Role"
  })
}

resource "aws_iam_role_policy_attachment" "ec2_runner_ssm_policy" {
  role       = aws_iam_role.ec2_runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ec2_runner_ecr_access" {
  name = "ECRAccess"
  role = aws_iam_role.ec2_runner_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ecr:*"]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "ec2_runner_self_terminate" {
  name = "SelfTerminate"
  role = aws_iam_role.ec2_runner_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ec2:TerminateInstances"]
      Resource = ["*"]
      Condition = {
        StringEquals = {
          "ec2:ResourceTag/ManagedBy" = local.ec2_runner_managed_by_tag
        }
      }
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_runner" {
  name = "GitHubSelfHostedRunnerInstanceProfile"
  role = aws_iam_role.ec2_runner_role.name

  tags = merge(local.common_tags, {
    Name = "GitHubSelfHostedRunnerInstanceProfile"
  })
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

  tags = merge(local.common_tags, {
    Name = "CatchAllHandler-ServiceRole"
  })
}

resource "aws_iam_role_policy_attachment" "lambda_catchall_handler_basic" {
  role       = aws_iam_role.lambda_catchall_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
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

  tags = merge(local.common_tags, {
    Name = "${var.lambda_function_name}-ServiceRole"
  })
}

resource "aws_iam_role_policy_attachment" "lambda_runners_handler_basic" {
  role       = aws_iam_role.lambda_runners_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_runners_handler_xray" {
  role       = aws_iam_role.lambda_runners_handler.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource "aws_iam_role_policy" "lambda_runners_handler_ssm" {
  name = "SSMParameterAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssm:GetParameter"]
      Resource = [
        aws_ssm_parameter.webhook_secret.arn,
        aws_ssm_parameter.api_key.arn
      ]
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
        Resource = [
          aws_sqs_queue.job_queue.arn,
          aws_sqs_queue.webhook_dlq.arn,
        ]
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
        aws_dynamodb_table.idempotency.arn,
        aws_dynamodb_table.workflow_runners.arn
      ]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_runners_handler_ssm_github_pat" {
  name = "SSMGitHubPATAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter"]
      Resource = [data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_runners_handler_ecs" {
  name = "ECSAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecs:StopTask",
        "ecs:DescribeTasks"
      ]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_runners_handler_ec2" {
  name = "EC2Access"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:TerminateInstances",
        "ec2:DescribeInstances"
      ]
      Resource = ["*"]
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

  tags = merge(local.common_tags, {
    Name = "V1ApiHandler-ServiceRole"
  })
}

resource "aws_iam_role_policy_attachment" "lambda_v1_handler_basic" {
  role       = aws_iam_role.lambda_v1_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
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
        "ecs:StopTask",
        "ecs:TagResource"
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
        "ec2:CreateFleet",
        "ec2:CreateLaunchTemplate",
        "ec2:CreateTags",
        "ec2:DeleteLaunchTemplate",
        "ec2:DeleteSnapshot",
        "ec2:DeregisterImage",
        "ec2:DescribeImages",
        "ec2:DescribeInstances",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSnapshots",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:RunInstances",
        "ec2:TerminateInstances"
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
      Resource = [data.terraform_remote_state.ecr.outputs.repository_arn]
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
        "arn:aws:ssm:${local.aws_region}:${local.aws_account_id}:parameter/github-runner/*",
        data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter,
        aws_ssm_parameter.api_key.arn
      ]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_v1_handler_kms" {
  name = "KMSDecrypt"
  role = aws_iam_role.lambda_v1_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_v1_handler_dynamodb" {
  name = "DynamoDBAccess"
  role = aws_iam_role.lambda_v1_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ]
      Resource = [aws_dynamodb_table.workflow_runners.arn]
    }]
  })
}

resource "aws_iam_role" "circuit_breaker_remediation" {
  name = "${local.resource_prefix}-CircuitBreakerRemediation-Role"

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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-CircuitBreakerRemediation-Role"
  })
}

resource "aws_iam_role_policy_attachment" "circuit_breaker_remediation_basic" {
  role       = aws_iam_role.circuit_breaker_remediation.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "circuit_breaker_remediation_permissions" {
  name = "RemediationPermissions"
  role = aws_iam_role.circuit_breaker_remediation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:ListEventSourceMappings",
          "lambda:UpdateEventSourceMapping",
          "lambda:PutFunctionConcurrency",
          "lambda:GetFunction",
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.runners_handler.arn,
          "arn:aws:lambda:${local.aws_region}:${local.aws_account_id}:event-source-mapping:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [aws_sns_topic.circuit_breaker_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = [
          aws_dynamodb_table.incidents.arn,
          aws_dynamodb_table.circuit_breaker_state.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role" "dlq_reprocessor" {
  name = "${local.resource_prefix}-DLQReprocessor-Role"

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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-DLQReprocessor-Role"
  })
}

resource "aws_iam_role_policy_attachment" "dlq_reprocessor_basic" {
  role       = aws_iam_role.dlq_reprocessor.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "dlq_reprocessor_permissions" {
  name = "DLQReprocessorPermissions"
  role = aws_iam_role.dlq_reprocessor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.webhook_dlq.arn,
          aws_sqs_queue.job_queue_dlq.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl"
        ]
        Resource = [aws_sqs_queue.job_queue.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [aws_sns_topic.circuit_breaker_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter]
      }
    ]
  })
}

resource "aws_iam_role" "circuit_breaker_recovery" {
  name = "${local.resource_prefix}-CircuitBreakerRecovery-Role"

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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-CircuitBreakerRecovery-Role"
  })
}

resource "aws_iam_role_policy_attachment" "circuit_breaker_recovery_basic" {
  role       = aws_iam_role.circuit_breaker_recovery.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "circuit_breaker_recovery_permissions" {
  name = "RecoveryPermissions"
  role = aws_iam_role.circuit_breaker_recovery.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:ListEventSourceMappings",
          "lambda:UpdateEventSourceMapping",
          "lambda:PutFunctionConcurrency",
          "lambda:DeleteFunctionConcurrency",
          "lambda:GetFunction",
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.runners_handler.arn,
          "arn:aws:lambda:${local.aws_region}:${local.aws_account_id}:event-source-mapping:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [aws_sns_topic.circuit_breaker_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [aws_dynamodb_table.circuit_breaker_state.arn]
      }
    ]
  })
}

resource "aws_iam_role" "drift_recovery" {
  name = "${local.resource_prefix}-DriftRecovery-Role"

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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-DriftRecovery-Role"
  })
}

resource "aws_iam_role_policy_attachment" "drift_recovery_basic" {
  role       = aws_iam_role.drift_recovery.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "drift_recovery_permissions" {
  name = "DriftRecoveryPermissions"
  role = aws_iam_role.drift_recovery.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [aws_sns_topic.circuit_breaker_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [aws_sqs_queue.drift_recovery.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups"
        ]
        Resource = ["*"]
      }
    ]
  })
}

resource "aws_iam_role" "spot_interruption_handler" {
  name = "${local.resource_prefix}-SpotInterruptionHandler-Role"

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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-SpotInterruptionHandler-Role"
  })
}

resource "aws_iam_role_policy_attachment" "spot_interruption_handler_basic" {
  role       = aws_iam_role.spot_interruption_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "spot_interruption_handler_permissions" {
  name = "SpotInterruptionHandlerPermissions"
  role = aws_iam_role.spot_interruption_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = [aws_dynamodb_table.workflow_runners.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances"
        ]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeTasks"
        ]
        Resource = ["*"]
        Condition = {
          ArnEquals = {
            "ecs:cluster" = aws_ecs_cluster.runner.arn
          }
        }
      }
    ]
  })
}

resource "aws_iam_role" "stale_runner_cleanup" {
  name = "${local.resource_prefix}-StaleRunnerCleanup-Role"

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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-StaleRunnerCleanup-Role"
  })
}

resource "aws_iam_role_policy_attachment" "stale_runner_cleanup_basic" {
  role       = aws_iam_role.stale_runner_cleanup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "stale_runner_cleanup_permissions" {
  name = "StaleRunnerCleanupPermissions"
  role = aws_iam_role.stale_runner_cleanup.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [data.terraform_remote_state.bootstrap.outputs.arn_for_github_pat_parameter]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:DeleteItem"
        ]
        Resource = [aws_dynamodb_table.workflow_runners.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:StopTask",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ]
        Resource = ["*"]
        Condition = {
          ArnEquals = {
            "ecs:cluster" = aws_ecs_cluster.runner.arn
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:TerminateInstances",
          "ec2:DescribeInstances"
        ]
        Resource = ["*"]
      }
    ]
  })
}
