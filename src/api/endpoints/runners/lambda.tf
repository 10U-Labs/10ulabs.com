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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
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
      CANCELLATION_QUEUE_URL     = aws_sqs_queue.cancellation.url
      CIRCUIT_BREAKER_TABLE_NAME = aws_dynamodb_table.circuit_breaker_state.name
      GITHUB_REPO                = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME   = module.shared.ssm_github_pat_name
      IDEMPOTENCY_TABLE_NAME     = aws_dynamodb_table.idempotency.name
      IGNORED_EVENTS_QUEUE_URL   = aws_sqs_queue.ignored_events.url
      JOB_QUEUE_URL              = aws_sqs_queue.job_queue.url
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

# Runner Starter Lambda - processes job_queue messages and starts runners
data "archive_file" "runner_starter" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/runner_starter.zip"

  source {
    content  = file("${path.module}/lambdas/runner_starter.py")
    filename = "runner_starter.py"
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "runner_starter" {
  filename                       = data.archive_file.runner_starter.output_path
  function_name                  = local.runner_starter_function_name
  role                           = aws_iam_role.runner_starter.arn
  handler                        = "runner_starter.lambda_handler"
  source_code_hash               = data.archive_file.runner_starter.output_base64sha256
  runtime                        = "python3.13"
  architectures                  = ["arm64"]
  timeout                        = local.lambda_timeout_seconds
  memory_size                    = local.lambda_memory_mb
  reserved_concurrent_executions = -1
  description                    = "Processes job queue messages and starts GitHub runners"

  environment {
    variables = {
      API_BASE_URL           = "https://${local.api_fqdn}"
      API_KEY_PARAMETER_NAME = data.terraform_remote_state.api.outputs.api_key_ssm_parameter
    }
  }

  tracing_config {
    mode = "Active"
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.runner_starter.name
  }

  tags = merge(local.common_tags, {
    Name = local.runner_starter_function_name
  })

  depends_on = [
    aws_iam_role_policy.runner_starter_ssm,
    aws_iam_role_policy.runner_starter_cloudwatch,
    aws_iam_role_policy.runner_starter_sqs,
    aws_iam_role_policy_attachment.runner_starter_basic,
    aws_iam_role_policy_attachment.runner_starter_xray,
  ]

  lifecycle {
    replace_triggered_by = [aws_iam_role.runner_starter.id]
  }
}

resource "aws_cloudwatch_log_group" "runner_starter" {
  name              = "/aws/lambda/${local.runner_starter_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.runner_starter_function_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "runner_starter_sqs" {
  event_source_arn                   = aws_sqs_queue.job_queue.arn
  function_name                      = aws_lambda_function.runner_starter.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}

# Runner Terminator Lambda - processes cancellation_queue and stops runners
data "archive_file" "runner_terminator" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/runner_terminator.zip"

  source {
    content  = file("${path.module}/lambdas/runner_terminator.py")
    filename = "runner_terminator.py"
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "runner_terminator" {
  filename                       = data.archive_file.runner_terminator.output_path
  function_name                  = local.runner_terminator_function_name
  role                           = aws_iam_role.runner_terminator.arn
  handler                        = "runner_terminator.lambda_handler"
  source_code_hash               = data.archive_file.runner_terminator.output_base64sha256
  runtime                        = "python3.13"
  architectures                  = ["arm64"]
  timeout                        = local.lambda_timeout_seconds
  memory_size                    = local.lambda_memory_mb
  reserved_concurrent_executions = -1
  description                    = "Processes cancellation queue and terminates GitHub runners"

  environment {
    variables = {
      EC2_MANAGED_BY_TAG = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_managed_by_tag
      ECS_CLUSTER        = data.terraform_remote_state.ecs_runner.outputs.cluster_arn
    }
  }

  tracing_config {
    mode = "Active"
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.runner_terminator.name
  }

  tags = merge(local.common_tags, {
    Name = local.runner_terminator_function_name
  })

  depends_on = [
    aws_iam_role_policy.runner_terminator_cloudwatch,
    aws_iam_role_policy.runner_terminator_sqs,
    aws_iam_role_policy.runner_terminator_ecs,
    aws_iam_role_policy.runner_terminator_ec2,
    aws_iam_role_policy_attachment.runner_terminator_basic,
    aws_iam_role_policy_attachment.runner_terminator_xray,
  ]

  lifecycle {
    replace_triggered_by = [aws_iam_role.runner_terminator.id]
  }
}

resource "aws_cloudwatch_log_group" "runner_terminator" {
  name              = "/aws/lambda/${local.runner_terminator_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.runner_terminator_function_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "runner_terminator_sqs" {
  event_source_arn                   = aws_sqs_queue.cancellation.arn
  function_name                      = aws_lambda_function.runner_terminator.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}

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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
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
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
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
      WEBHOOK_DLQ_URL             = aws_sqs_queue.webhook_dlq.url
      JOB_DLQ_URL                 = aws_sqs_queue.job_queue_dlq.url
      JOB_QUEUE_URL               = aws_sqs_queue.job_queue.url
      SNS_TOPIC_ARN               = aws_sns_topic.circuit_breaker_alerts.arn
      GITHUB_TOKEN_PARAMETER_NAME = module.shared.ssm_github_pat_name
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
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

data "archive_file" "drift_recovery" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/drift_recovery.zip"

  source {
    content  = file("${path.module}/lambdas/drift_recovery.py")
    filename = "drift_recovery.py"
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "drift_recovery" {
  filename         = data.archive_file.drift_recovery.output_path
  function_name    = local.drift_recovery_function_name
  role             = aws_iam_role.drift_recovery.arn
  handler          = "drift_recovery.lambda_handler"
  source_code_hash = data.archive_file.drift_recovery.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 30
  memory_size      = 256
  description      = "Triggers API workflow when infrastructure drift is detected"

  environment {
    variables = {
      GITHUB_REPO                 = local.github_repo_full
      GITHUB_TOKEN_PARAMETER_NAME = module.shared.ssm_github_pat_name
      SNS_TOPIC_ARN               = aws_sns_topic.circuit_breaker_alerts.arn
      MANAGED_VPC_ID              = data.terraform_remote_state.api_shared_runners.outputs.vpc_id
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.drift_recovery.name
  }

  tags = merge(local.common_tags, {
    Name = local.drift_recovery_function_name
  })

  depends_on = [
    aws_iam_role_policy.drift_recovery_permissions,
    aws_iam_role_policy_attachment.drift_recovery_basic,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.drift_recovery.id]
  }
}

resource "aws_cloudwatch_log_group" "drift_recovery" {
  name              = "/aws/lambda/${local.drift_recovery_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.drift_recovery_function_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "drift_recovery_sqs" {
  event_source_arn = aws_sqs_queue.drift_recovery.arn
  function_name    = aws_lambda_function.drift_recovery.arn
  batch_size       = 1
}

data "archive_file" "spot_interruption_handler" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/spot_interruption_handler.zip"

  source {
    content  = file("${path.module}/lambdas/spot_interruption_handler.py")
    filename = "spot_interruption_handler.py"
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "spot_interruption_handler" {
  filename         = data.archive_file.spot_interruption_handler.output_path
  function_name    = local.spot_interruption_handler_function_name
  role             = aws_iam_role.spot_interruption_handler.arn
  handler          = "spot_interruption_handler.lambda_handler"
  source_code_hash = data.archive_file.spot_interruption_handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 60
  memory_size      = 256
  description      = "Handles spot interruption events and launches replacement runners"

  environment {
    variables = {
      API_BASE_URL             = "https://${local.api_fqdn}"
      API_KEY_PARAMETER_NAME   = data.terraform_remote_state.api.outputs.api_key_ssm_parameter
      ECS_CLUSTER              = data.terraform_remote_state.ecs_runner.outputs.cluster_arn
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = module.shared.ssm_github_pat_name
      WORKFLOW_RUNNERS_TABLE   = aws_dynamodb_table.workflow_runners.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.spot_interruption_handler.name
  }

  tags = merge(local.common_tags, {
    Name = local.spot_interruption_handler_function_name
  })

  depends_on = [
    aws_iam_role_policy.spot_interruption_handler_permissions,
    aws_iam_role_policy_attachment.spot_interruption_handler_basic,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.spot_interruption_handler.id]
  }
}

resource "aws_cloudwatch_log_group" "spot_interruption_handler" {
  name              = "/aws/lambda/${local.spot_interruption_handler_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.spot_interruption_handler_function_name}Logs"
  })
}

data "archive_file" "stale_runner_cleanup" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/stale_runner_cleanup.zip"

  source {
    content  = file("${path.module}/lambdas/stale_runner_cleanup.py")
    filename = "stale_runner_cleanup.py"
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
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${local.etc_dir}/runners.json")
    filename = "etc/runners.json"
  }
}

resource "aws_lambda_function" "stale_runner_cleanup" {
  filename         = data.archive_file.stale_runner_cleanup.output_path
  function_name    = local.stale_runner_cleanup_function_name
  role             = aws_iam_role.stale_runner_cleanup.arn
  handler          = "stale_runner_cleanup.lambda_handler"
  source_code_hash = data.archive_file.stale_runner_cleanup.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 300
  memory_size      = 256
  description      = "Cleans up stale runners from completed or failed workflows"

  environment {
    variables = {
      EC2_MANAGED_BY_TAG       = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_managed_by_tag
      ECS_CLUSTER              = data.terraform_remote_state.ecs_runner.outputs.cluster_arn
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = module.shared.ssm_github_pat_name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.stale_runner_cleanup.name
  }

  tags = merge(local.common_tags, {
    Name = local.stale_runner_cleanup_function_name
  })

  depends_on = [
    aws_iam_role_policy.stale_runner_cleanup_permissions,
    aws_iam_role_policy_attachment.stale_runner_cleanup_basic,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.stale_runner_cleanup.id]
  }
}

resource "aws_cloudwatch_log_group" "stale_runner_cleanup" {
  name              = "/aws/lambda/${local.stale_runner_cleanup_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.stale_runner_cleanup_function_name}Logs"
  })
}

# Health Check Lambda - lightweight liveness check with no AWS dependencies
data "archive_file" "health_check" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/health_check.zip"

  source {
    content  = file("${path.module}/lambdas/health_check.py")
    filename = "health_check.py"
  }
}

resource "aws_lambda_function" "health_check" {
  filename         = data.archive_file.health_check.output_path
  function_name    = local.health_check_function_name
  role             = aws_iam_role.health_check.arn
  handler          = "health_check.lambda_handler"
  source_code_hash = data.archive_file.health_check.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128
  description      = "Lightweight health check for runners service"

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.health_check.name
  }

  tags = merge(local.common_tags, {
    Name = local.health_check_function_name
  })

  depends_on = [
    aws_iam_role_policy_attachment.health_check_basic,
  ]

  lifecycle {
    replace_triggered_by = [aws_iam_role.health_check.id]
  }
}

resource "aws_cloudwatch_log_group" "health_check" {
  name              = "/aws/lambda/${local.health_check_function_name}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.health_check_function_name}Logs"
  })
}

resource "aws_lambda_permission" "health_check_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.runners_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}
