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

resource "aws_iam_role_policy" "lambda_runners_handler_ssm" {
  name = "SSMParameterAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssm:GetParameter"]
      Resource = [
        aws_ssm_parameter.webhook_secret.arn
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
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = [
        aws_sqs_queue.webhook_dlq.arn,
      ]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_runners_handler_s3" {
  name = "S3ArchiveAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:PutObject"
      ]
      Resource = ["${aws_s3_bucket.ignored_events_archive.arn}/*"]
    }]
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

resource "aws_iam_role_policy" "lambda_runners_handler_ssm_github_pat" {
  name = "SSMGitHubPATAccess"
  role = aws_iam_role.lambda_runners_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter"]
      Resource = [module.common.ssm_github_pat_arn]
    }]
  })
}

# KMS access for decrypting Lambda environment variables
# This explicit IAM policy prevents stale KMS grant issues when IAM roles are recreated.
# KMS grants are tied to role unique IDs which change on recreation; IAM policies are not.
resource "aws_iam_role_policy" "lambda_runners_handler_kms" {
  name = "KMSDecrypt"
  role = aws_iam_role.lambda_runners_handler.id

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

resource "aws_iam_role" "circuit_opens" {
  name = local.circuit_opens_role_name

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
    Name = local.circuit_opens_role_name
  })
}

resource "aws_iam_role_policy_attachment" "circuit_opens_basic" {
  role       = aws_iam_role.circuit_opens.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "circuit_opens_permissions" {
  name = "ResetPermissions"
  role = aws_iam_role.circuit_opens.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:UpdateEventSourceMapping",
          "lambda:DeleteFunctionConcurrency",
          "lambda:GetFunctionConcurrency"
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
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = [aws_dynamodb_table.circuit_open_state.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "circuit_opens_kms" {
  name = "KMSDecrypt"
  role = aws_iam_role.circuit_opens.id

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

resource "aws_iam_role" "circuit_open_remediations" {
  name = local.circuit_open_remediations_role_name

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
    Name = local.circuit_open_remediations_role_name
  })
}

resource "aws_iam_role_policy_attachment" "circuit_open_remediations_basic" {
  role       = aws_iam_role.circuit_open_remediations.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "circuit_open_remediations_permissions" {
  name = "RemediationPermissions"
  role = aws_iam_role.circuit_open_remediations.id

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
        Resource = [aws_sns_topic.circuit_open_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = [
          aws_dynamodb_table.incidents.arn,
          aws_dynamodb_table.circuit_open_state.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "circuit_open_remediations_kms" {
  name = "KMSDecrypt"
  role = aws_iam_role.circuit_open_remediations.id

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
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [aws_sns_topic.circuit_open_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = [module.common.ssm_github_pat_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "dlq_reprocessor_kms" {
  name = "KMSDecrypt"
  role = aws_iam_role.dlq_reprocessor.id

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

resource "aws_iam_role" "circuit_open_recoveries" {
  name = local.circuit_open_recoveries_role_name

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
    Name = local.circuit_open_recoveries_role_name
  })
}

resource "aws_iam_role_policy_attachment" "circuit_open_recoveries_basic" {
  role       = aws_iam_role.circuit_open_recoveries.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "circuit_open_recoveries_permissions" {
  name = "RecoveryPermissions"
  role = aws_iam_role.circuit_open_recoveries.id

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
        Resource = [aws_sns_topic.circuit_open_alerts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [aws_dynamodb_table.circuit_open_state.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "circuit_open_recoveries_kms" {
  name = "KMSDecrypt"
  role = aws_iam_role.circuit_open_recoveries.id

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
