data "archive_file" "runners_handler" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/runners_handler.zip"

  source {
    content  = file("${path.module}/lambdas/webhook_router.py")
    filename = "webhook_router.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/__init__.py")
    filename = "common/__init__.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/aws_clients.py")
    filename = "common/aws_clients.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/circuit_breaker_utils.py")
    filename = "common/circuit_breaker_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/cloudwatch.py")
    filename = "common/cloudwatch.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ec2_utils.py")
    filename = "common/ec2_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ecs_utils.py")
    filename = "common/ecs_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/github_api.py")
    filename = "common/github_api.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/lambda_utils.py")
    filename = "common/lambda_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/webhook_ingress.py")
    filename = "common/webhook_ingress.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${path.module}/../../../../../etc/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "runners_handler" {
  filename                       = data.archive_file.runners_handler.output_path
  function_name                  = local.webhook_handler_function_name
  role                           = aws_iam_role.lambda_runners_handler.arn
  handler                        = "webhook_router.lambda_handler"
  source_code_hash               = data.archive_file.runners_handler.output_base64sha256
  runtime                        = "python3.13"
  architectures                  = ["arm64"]
  timeout                        = local.lambda_timeout_seconds
  memory_size                    = local.lambda_memory_mb
  reserved_concurrent_executions = -1
  description                    = "GitHub webhook router for GitHub self-hosted runners"

  environment {
    variables = {
      API_BASE_URL               = "https://${local.api_fqdn}"
      API_KEY_PARAMETER_NAME     = data.terraform_remote_state.api.outputs.api_key_ssm_parameter
      CIRCUIT_BREAKER_TABLE_NAME = aws_dynamodb_table.circuit_breaker_state.name
      GITHUB_REPO                = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME   = module.common.ssm_github_pat_name
      IDEMPOTENCY_TABLE_NAME     = aws_dynamodb_table.idempotency.name
      IGNORED_EVENTS_QUEUE_URL   = aws_sqs_queue.ignored_events.url
      WEBHOOK_SECRET_NAME        = aws_ssm_parameter.webhook_secret.name
    }
  }

  dead_letter_config {
    target_arn = aws_sqs_queue.webhook_dlq.arn
  }

  tracing_config {
    mode = "Active"
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.runners_handler.name
  }

  tags = merge(local.common_tags, {
    Name = local.webhook_handler_function_name
  })

  depends_on = [
    aws_iam_role_policy.lambda_runners_handler_ssm,
    aws_iam_role_policy.lambda_runners_handler_cloudwatch,
    aws_iam_role_policy.lambda_runners_handler_sqs,
    aws_iam_role_policy.lambda_runners_handler_dynamodb,
    aws_iam_role_policy.lambda_runners_handler_ssm_github_pat,
    aws_iam_role_policy_attachment.lambda_runners_handler_basic,
    aws_iam_role_policy_attachment.lambda_runners_handler_xray,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda_runners_handler.id]
  }
}

resource "aws_cloudwatch_log_group" "runners_handler" {
  name              = local.webhook_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.webhook_handler_function_name}Logs"
  })
}

# Event source mapping for webhook ingress queue (API Gateway → SQS → Lambda)
# This is the entry point for GitHub webhooks after removing Lambda from the API Gateway hot path
resource "aws_lambda_event_source_mapping" "runners_handler_webhook_ingress" {
  event_source_arn                   = aws_sqs_queue.webhook_ingress.arn
  function_name                      = aws_lambda_function.runners_handler.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}

# Note: runner_starter Lambda removed - routing logic moved to /v1/runners endpoint
# Note: runner_terminator Lambda removed - runners are ephemeral and self-terminate

# Ignored Events Archiver Lambda - archives ignored events to S3
data "archive_file" "ignored_events_archiver" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/ignored_events_archiver.zip"

  source {
    content  = file("${path.module}/lambdas/ignored_events_archiver.py")
    filename = "ignored_events_archiver.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/__init__.py")
    filename = "common/__init__.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/aws_clients.py")
    filename = "common/aws_clients.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/circuit_breaker_utils.py")
    filename = "common/circuit_breaker_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/cloudwatch.py")
    filename = "common/cloudwatch.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ec2_utils.py")
    filename = "common/ec2_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ecs_utils.py")
    filename = "common/ecs_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/github_api.py")
    filename = "common/github_api.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/lambda_utils.py")
    filename = "common/lambda_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/webhook_ingress.py")
    filename = "common/webhook_ingress.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "ignored_events_archiver" {
  filename                       = data.archive_file.ignored_events_archiver.output_path
  function_name                  = local.ignored_events_archiver_function_name
  role                           = aws_iam_role.ignored_events_archiver.arn
  handler                        = "ignored_events_archiver.lambda_handler"
  source_code_hash               = data.archive_file.ignored_events_archiver.output_base64sha256
  runtime                        = "python3.13"
  architectures                  = ["arm64"]
  timeout                        = 60
  memory_size                    = 256
  reserved_concurrent_executions = -1
  description                    = "Archives ignored webhook events to S3 for long-term storage"

  environment {
    variables = {
      ARCHIVE_BUCKET_NAME = aws_s3_bucket.ignored_events_archive.bucket
    }
  }

  tracing_config {
    mode = "Active"
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.ignored_events_archiver.name
  }

  tags = merge(local.common_tags, {
    Name = local.ignored_events_archiver_function_name
  })

  depends_on = [
    aws_iam_role_policy.ignored_events_archiver_cloudwatch,
    aws_iam_role_policy.ignored_events_archiver_sqs,
    aws_iam_role_policy.ignored_events_archiver_s3,
    aws_iam_role_policy_attachment.ignored_events_archiver_basic,
    aws_iam_role_policy_attachment.ignored_events_archiver_xray,
  ]

  lifecycle {
    replace_triggered_by = [aws_iam_role.ignored_events_archiver.id]
  }
}

resource "aws_cloudwatch_log_group" "ignored_events_archiver" {
  name              = "/aws/lambda/${local.ignored_events_archiver_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.ignored_events_archiver_function_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "ignored_events_archiver_sqs" {
  event_source_arn                   = aws_sqs_queue.ignored_events.arn
  function_name                      = aws_lambda_function.ignored_events_archiver.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 60
}

data "archive_file" "circuit_breaker_reset" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/circuit_breaker_reset.zip"

  source {
    content  = file("${path.module}/lambdas/circuit_breaker_reset.py")
    filename = "circuit_breaker_reset.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/__init__.py")
    filename = "common/__init__.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/aws_clients.py")
    filename = "common/aws_clients.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/circuit_breaker_utils.py")
    filename = "common/circuit_breaker_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/cloudwatch.py")
    filename = "common/cloudwatch.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ec2_utils.py")
    filename = "common/ec2_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ecs_utils.py")
    filename = "common/ecs_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/github_api.py")
    filename = "common/github_api.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/lambda_utils.py")
    filename = "common/lambda_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/webhook_ingress.py")
    filename = "common/webhook_ingress.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "circuit_breaker_reset" {
  filename         = data.archive_file.circuit_breaker_reset.output_path
  function_name    = local.circuit_breaker_reset_function_name
  role             = aws_iam_role.circuit_breaker_reset.arn
  handler          = "circuit_breaker_reset.lambda_handler"
  source_code_hash = data.archive_file.circuit_breaker_reset.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 60
  memory_size      = 256
  description      = "Manual reset endpoint for circuit breaker"


  environment {
    variables = {
      WEBHOOK_FUNCTION_NAME = aws_lambda_function.runners_handler.function_name
      STATE_TABLE_NAME      = aws_dynamodb_table.circuit_breaker_state.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.circuit_breaker_reset.name
  }

  tags = merge(local.common_tags, {
    Name = local.circuit_breaker_reset_function_name
  })

  depends_on = [
    aws_iam_role_policy.circuit_breaker_reset_permissions,
    aws_iam_role_policy_attachment.circuit_breaker_reset_basic,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.circuit_breaker_reset.id]
  }
}

resource "aws_cloudwatch_log_group" "circuit_breaker_reset" {
  name              = "/aws/lambda/${local.circuit_breaker_reset_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.circuit_breaker_reset_function_name}Logs"
  })
}

resource "aws_lambda_permission" "circuit_breaker_reset_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.circuit_breaker_reset.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_id}/*"
}

data "archive_file" "circuit_breaker_remediation" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/circuit_breaker_remediation.zip"

  source {
    content  = file("${path.module}/lambdas/circuit_breaker_remediation.py")
    filename = "circuit_breaker_remediation.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/__init__.py")
    filename = "common/__init__.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/aws_clients.py")
    filename = "common/aws_clients.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/circuit_breaker_utils.py")
    filename = "common/circuit_breaker_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/cloudwatch.py")
    filename = "common/cloudwatch.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ec2_utils.py")
    filename = "common/ec2_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ecs_utils.py")
    filename = "common/ecs_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/github_api.py")
    filename = "common/github_api.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/lambda_utils.py")
    filename = "common/lambda_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/webhook_ingress.py")
    filename = "common/webhook_ingress.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "circuit_breaker_remediation" {
  filename         = data.archive_file.circuit_breaker_remediation.output_path
  function_name    = local.circuit_breaker_remediation_function_name
  role             = aws_iam_role.circuit_breaker_remediation.arn
  handler          = "circuit_breaker_remediation.lambda_handler"
  source_code_hash = data.archive_file.circuit_breaker_remediation.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 60
  memory_size      = 256
  description      = "Automatic remediation for circuit breaker alarms"


  environment {
    variables = {
      WEBHOOK_FUNCTION_NAME = aws_lambda_function.runners_handler.function_name
      SNS_TOPIC_ARN         = aws_sns_topic.circuit_breaker_alerts.arn
      INCIDENT_TABLE_NAME   = aws_dynamodb_table.incidents.name
      STATE_TABLE_NAME      = aws_dynamodb_table.circuit_breaker_state.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.circuit_breaker_remediation.name
  }

  tags = merge(local.common_tags, {
    Name = local.circuit_breaker_remediation_function_name
  })

  depends_on = [
    aws_iam_role_policy.circuit_breaker_remediation_permissions,
    aws_iam_role_policy_attachment.circuit_breaker_remediation_basic,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.circuit_breaker_remediation.id]
  }
}

resource "aws_cloudwatch_log_group" "circuit_breaker_remediation" {
  name              = "/aws/lambda/${local.circuit_breaker_remediation_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.circuit_breaker_remediation_function_name}Logs"
  })
}

data "archive_file" "dlq_reprocessor" {
  type        = "zip"
  source_file = "${path.module}/lambdas/dlq_reprocessor.py"
  output_path = "${path.module}/.terraform/lambda_packages/dlq_reprocessor.zip"
}

resource "aws_lambda_function" "dlq_reprocessor" {
  filename         = data.archive_file.dlq_reprocessor.output_path
  function_name    = local.dlq_reprocessor_function_name
  role             = aws_iam_role.dlq_reprocessor.arn
  handler          = "dlq_reprocessor.handler"
  source_code_hash = data.archive_file.dlq_reprocessor.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 300
  memory_size      = 256
  description      = "Reprocesses messages from DLQs"


  environment {
    variables = {
      WEBHOOK_DLQ_URL = aws_sqs_queue.webhook_dlq.url
      # Note: JOB_DLQ_URL and JOB_QUEUE_URL removed - routing logic moved to /v1/runners
      SNS_TOPIC_ARN               = aws_sns_topic.circuit_breaker_alerts.arn
      GITHUB_TOKEN_PARAMETER_NAME = module.common.ssm_github_pat_name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.dlq_reprocessor.name
  }

  tags = merge(local.common_tags, {
    Name = local.dlq_reprocessor_function_name
  })

  depends_on = [
    aws_iam_role_policy.dlq_reprocessor_permissions,
    aws_iam_role_policy_attachment.dlq_reprocessor_basic,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.dlq_reprocessor.id]
  }
}

resource "aws_cloudwatch_log_group" "dlq_reprocessor" {
  name              = "/aws/lambda/${local.dlq_reprocessor_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.dlq_reprocessor_function_name}Logs"
  })
}

data "archive_file" "circuit_breaker_recovery" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/circuit_breaker_recovery.zip"

  source {
    content  = file("${path.module}/lambdas/circuit_breaker_recovery.py")
    filename = "circuit_breaker_recovery.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/__init__.py")
    filename = "common/__init__.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/aws_clients.py")
    filename = "common/aws_clients.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/circuit_breaker_utils.py")
    filename = "common/circuit_breaker_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/cloudwatch.py")
    filename = "common/cloudwatch.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ec2_utils.py")
    filename = "common/ec2_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/ecs_utils.py")
    filename = "common/ecs_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/github_api.py")
    filename = "common/github_api.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/lambda_utils.py")
    filename = "common/lambda_utils.py"
  }
  source {
    content  = file("${path.module}/lambdas/common/webhook_ingress.py")
    filename = "common/webhook_ingress.py"
  }
  source {
    content  = file("${path.module}/../../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "circuit_breaker_recovery" {
  filename         = data.archive_file.circuit_breaker_recovery.output_path
  function_name    = local.circuit_breaker_recovery_function_name
  role             = aws_iam_role.circuit_breaker_recovery.arn
  handler          = "circuit_breaker_recovery.lambda_handler"
  source_code_hash = data.archive_file.circuit_breaker_recovery.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 60
  memory_size      = 256
  description      = "Automatic self-healing recovery for circuit breaker"


  environment {
    variables = {
      WEBHOOK_FUNCTION_NAME = aws_lambda_function.runners_handler.function_name
      STATE_TABLE_NAME      = aws_dynamodb_table.circuit_breaker_state.name
      SNS_TOPIC_ARN         = aws_sns_topic.circuit_breaker_alerts.arn
      MAX_RECOVERY_ATTEMPTS = "5"
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.circuit_breaker_recovery.name
  }

  tags = merge(local.common_tags, {
    Name = local.circuit_breaker_recovery_function_name
  })

  depends_on = [
    aws_iam_role_policy.circuit_breaker_recovery_permissions,
    aws_iam_role_policy_attachment.circuit_breaker_recovery_basic,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.circuit_breaker_recovery.id]
  }
}

resource "aws_cloudwatch_log_group" "circuit_breaker_recovery" {
  name              = "/aws/lambda/${local.circuit_breaker_recovery_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.circuit_breaker_recovery_function_name}Logs"
  })
}

# Note: drift_recovery Lambda removed - migrated to /v1/drift-recoveries endpoint

# Note: spot_interruption_handler Lambda removed - migrated to /v1/ec2-spot-interruptions and /v1/ecs-task-stops endpoints

# Note: stale_runner_cleanup Lambda removed - migrated to /v1/runners/cleanups endpoint

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.runners_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_id}/*"
}
