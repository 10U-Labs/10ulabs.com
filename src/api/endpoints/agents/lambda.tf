# Agent Lambdas - Single-responsibility handlers consuming from SQS
#
# All Lambdas are protected by SQS - defensive architecture regardless of trigger source.
# Each Lambda has a single responsibility and consumes from its own SQS queue.

locals {
  # Common Lambda settings
  lambda_runtime      = "nodejs22.x"
  lambda_architecture = "arm64"
  lambda_timeout      = 120
  lambda_memory       = 256

  # Common environment variables for all Lambdas
  common_env_vars = {
    AGENT_RUNTIME_ARN          = aws_bedrockagentcore_agent_runtime.runtime.agent_runtime_arn
    AWS_REGION_NAME            = local.aws_region
    GITHUB_ORG                 = module.shared.github_org
    GITHUB_REPO                = module.shared.name_for_github_repo
    SSM_GITHUB_APP_ID          = local.github_app_ssm.id
    SSM_GITHUB_APP_INSTALL_ID  = local.github_app_ssm.installation_id
    SSM_GITHUB_APP_PRIVATE_KEY = local.github_app_ssm.private_key
  }
}

# =============================================================================
# Webhook Lambda - Processes GitHub workflow failure events
# =============================================================================

data "archive_file" "webhook_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambdas/webhook.js"
  output_path = "${path.module}/.terraform/lambda_packages/webhook.zip"
}

resource "aws_lambda_function" "webhook" {
  filename                       = data.archive_file.webhook_lambda.output_path
  function_name                  = local.webhook_lambda_name
  role                           = aws_iam_role.webhook_lambda.arn
  handler                        = "webhook.handler"
  source_code_hash               = data.archive_file.webhook_lambda.output_base64sha256
  runtime                        = local.lambda_runtime
  architectures                  = [local.lambda_architecture]
  timeout                        = local.lambda_timeout
  memory_size                    = local.lambda_memory
  reserved_concurrent_executions = 2 # Limit parallel invocations to prevent Bedrock throttling
  description                    = "Agent webhook handler - processes GitHub workflow failures"
  layers                         = [aws_lambda_layer_version.github_auth.arn]

  environment {
    variables = local.common_env_vars
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.webhook_lambda.name
  }

  tags = merge(local.common_tags, {
    Name = local.webhook_lambda_name
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.webhook_lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "webhook_lambda" {
  name              = "/aws/lambda/${local.webhook_lambda_name}"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.webhook_lambda_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "webhook_sqs" {
  event_source_arn                   = aws_sqs_queue.webhook_ingress.arn
  function_name                      = aws_lambda_function.webhook.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0

  function_response_types = ["ReportBatchItemFailures"]
}

# =============================================================================
# Scanner Lambda - Scans for unresolved workflow failures
# =============================================================================

data "archive_file" "scanner_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambdas/scanner.js"
  output_path = "${path.module}/.terraform/lambda_packages/scanner.zip"
}

resource "aws_lambda_function" "scanner" {
  filename         = data.archive_file.scanner_lambda.output_path
  function_name    = local.scanner_lambda_name
  role             = aws_iam_role.webhook_lambda.arn # Reuse same role
  handler          = "scanner.handler"
  source_code_hash = data.archive_file.scanner_lambda.output_base64sha256
  runtime          = local.lambda_runtime
  architectures    = [local.lambda_architecture]
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory
  description      = "Agent scanner - scans for unresolved workflow failures"
  layers           = [aws_lambda_layer_version.github_auth.arn]

  environment {
    variables = local.common_env_vars
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.scanner_lambda.name
  }

  tags = merge(local.common_tags, {
    Name = local.scanner_lambda_name
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.webhook_lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "scanner_lambda" {
  name              = "/aws/lambda/${local.scanner_lambda_name}"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.scanner_lambda_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "scanner_sqs" {
  event_source_arn                   = aws_sqs_queue.scanner.arn
  function_name                      = aws_lambda_function.scanner.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0

  function_response_types = ["ReportBatchItemFailures"]
}

# =============================================================================
# Invoker Lambda - Handles direct agent invocations
# =============================================================================

data "archive_file" "invoker_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambdas/invoker.js"
  output_path = "${path.module}/.terraform/lambda_packages/invoker.zip"
}

resource "aws_lambda_function" "invoker" {
  filename         = data.archive_file.invoker_lambda.output_path
  function_name    = local.invoker_lambda_name
  role             = aws_iam_role.webhook_lambda.arn # Reuse same role
  handler          = "invoker.handler"
  source_code_hash = data.archive_file.invoker_lambda.output_base64sha256
  runtime          = local.lambda_runtime
  architectures    = [local.lambda_architecture]
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory
  description      = "Agent invoker - handles direct agent invocations"
  layers           = [aws_lambda_layer_version.github_auth.arn]

  environment {
    variables = local.common_env_vars
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.invoker_lambda.name
  }

  tags = merge(local.common_tags, {
    Name = local.invoker_lambda_name
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.webhook_lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "invoker_lambda" {
  name              = "/aws/lambda/${local.invoker_lambda_name}"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.invoker_lambda_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "invoker_sqs" {
  event_source_arn                   = aws_sqs_queue.invoker_ingress.arn
  function_name                      = aws_lambda_function.invoker.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0

  function_response_types = ["ReportBatchItemFailures"]
}
