resource "aws_iam_role" "lambda_runners_handler" {
  name = local.lambda_runners_handler_role_name

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
    Name = local.lambda_runners_handler_role_name
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
        data.terraform_remote_state.api.outputs.api_key_ssm_parameter_arn
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
      Resource = [module.shared.ssm_github_pat_arn]
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

resource "aws_iam_role" "circuit_breaker_remediation" {
  name = local.circuit_breaker_remediation_role_name

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
    Name = local.circuit_breaker_remediation_role_name
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
        Effect   = "Allow"
        Action   = ["lambda:ListEventSourceMappings"]
        Resource = ["*"]
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
  name = local.dlq_reprocessor_role_name

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
    Name = local.dlq_reprocessor_role_name
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
        Resource = [module.shared.ssm_github_pat_arn]
      }
    ]
  })
}

resource "aws_iam_role" "circuit_breaker_recovery" {
  name = local.circuit_breaker_recovery_role_name

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
    Name = local.circuit_breaker_recovery_role_name
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
        Effect   = "Allow"
        Action   = ["lambda:ListEventSourceMappings"]
        Resource = ["*"]
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
  name = local.drift_recovery_role_name

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
    Name = local.drift_recovery_role_name
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
        Resource = [module.shared.ssm_github_pat_arn]
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
  name = local.spot_interruption_handler_role_name

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
    Name = local.spot_interruption_handler_role_name
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
    Statement = concat(
      [
        {
          Effect = "Allow"
          Action = [
            "ssm:GetParameter"
          ]
          Resource = [
            module.shared.ssm_github_pat_arn,
            data.terraform_remote_state.api.outputs.api_key_ssm_parameter_arn
          ]
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
        }
      ],
      # ECS statement only when cluster exists (empty ARN causes malformed policy)
      data.terraform_remote_state.ecs_runner.outputs.cluster_arn != "" ? [
        {
          Effect = "Allow"
          Action = [
            "ecs:DescribeTasks"
          ]
          Resource = ["*"]
          Condition = {
            ArnEquals = {
              "ecs:cluster" = data.terraform_remote_state.ecs_runner.outputs.cluster_arn
            }
          }
        }
      ] : []
    )
  })
}

resource "aws_iam_role" "stale_runner_cleanup" {
  name = local.stale_runner_cleanup_role_name

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
    Name = local.stale_runner_cleanup_role_name
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
    Statement = concat(
      [
        {
          Effect = "Allow"
          Action = [
            "ssm:GetParameter"
          ]
          Resource = [module.shared.ssm_github_pat_arn]
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
            "ec2:TerminateInstances",
            "ec2:DescribeInstances"
          ]
          Resource = ["*"]
        }
      ],
      # ECS statement only when cluster exists (empty ARN causes malformed policy)
      data.terraform_remote_state.ecs_runner.outputs.cluster_arn != "" ? [
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
              "ecs:cluster" = data.terraform_remote_state.ecs_runner.outputs.cluster_arn
            }
          }
        }
      ] : []
    )
  })
}
