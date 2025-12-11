data "archive_file" "runners_handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambdas/webhook_router.py")
    filename = "webhook_router.py"
  }
  source {
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  output_path = "${path.module}/.terraform/lambda_packages/runners_handler.zip"
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
      API_BASE_URL             = "https://${local.api_fqdn}"
      API_KEY_PARAMETER_NAME   = data.terraform_remote_state.api.outputs.api_key_ssm_parameter
      ECS_CLUSTER              = data.terraform_remote_state.ecs_runner.outputs.cluster_arn
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = module.shared.ssm_github_pat_name
      IDEMPOTENCY_TABLE_NAME   = aws_dynamodb_table.idempotency.name
      JOB_QUEUE_URL            = aws_sqs_queue.job_queue.url
      WEBHOOK_SECRET_NAME      = aws_ssm_parameter.webhook_secret.name
      WORKFLOW_RUNNERS_TABLE   = aws_dynamodb_table.workflow_runners.name
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
    aws_iam_role_policy.lambda_runners_handler_ecs,
    aws_iam_role_policy.lambda_runners_handler_ec2,
    aws_iam_role_policy_attachment.lambda_runners_handler_basic,
    aws_iam_role_policy_attachment.lambda_runners_handler_xray,
  ]
}

resource "aws_cloudwatch_log_group" "runners_handler" {
  name              = local.webhook_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.webhook_handler_function_name}Logs"
  })
}

resource "aws_lambda_event_source_mapping" "runners_handler_sqs" {
  event_source_arn                   = aws_sqs_queue.job_queue.arn
  function_name                      = aws_lambda_function.runners_handler.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}

data "archive_file" "circuit_breaker_remediation" {
  type        = "zip"
  source_file = "${path.module}/lambdas/circuit_breaker_remediation.py"
  output_path = "${path.module}/.terraform/lambda_packages/circuit_breaker_remediation.zip"
}

resource "aws_lambda_function" "circuit_breaker_remediation" {
  filename         = data.archive_file.circuit_breaker_remediation.output_path
  function_name    = "${local.resource_prefix}CircuitBreakerRemediation"
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
    Name = "${local.resource_prefix}CircuitBreakerRemediation"
  })

  depends_on = [
    aws_iam_role_policy.circuit_breaker_remediation_permissions,
    aws_iam_role_policy_attachment.circuit_breaker_remediation_basic,
  ]
}

resource "aws_cloudwatch_log_group" "circuit_breaker_remediation" {
  name              = "/aws/lambda/${local.resource_prefix}CircuitBreakerRemediation"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}CircuitBreakerRemediationLogs"
  })
}

data "archive_file" "dlq_reprocessor" {
  type        = "zip"
  source_file = "${path.module}/lambdas/dlq_reprocessor.py"
  output_path = "${path.module}/.terraform/lambda_packages/dlq_reprocessor.zip"
}

resource "aws_lambda_function" "dlq_reprocessor" {
  filename         = data.archive_file.dlq_reprocessor.output_path
  function_name    = "${local.resource_prefix}DLQReprocessor"
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
    Name = "${local.resource_prefix}DLQReprocessor"
  })

  depends_on = [
    aws_iam_role_policy.dlq_reprocessor_permissions,
    aws_iam_role_policy_attachment.dlq_reprocessor_basic,
  ]
}

resource "aws_cloudwatch_log_group" "dlq_reprocessor" {
  name              = "/aws/lambda/${local.resource_prefix}DLQReprocessor"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}DLQReprocessorLogs"
  })
}

data "archive_file" "circuit_breaker_recovery" {
  type        = "zip"
  source_file = "${path.module}/lambdas/circuit_breaker_recovery.py"
  output_path = "${path.module}/.terraform/lambda_packages/circuit_breaker_recovery.zip"
}

resource "aws_lambda_function" "circuit_breaker_recovery" {
  filename         = data.archive_file.circuit_breaker_recovery.output_path
  function_name    = "${local.resource_prefix}CircuitBreakerRecovery"
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
    Name = "${local.resource_prefix}CircuitBreakerRecovery"
  })

  depends_on = [
    aws_iam_role_policy.circuit_breaker_recovery_permissions,
    aws_iam_role_policy_attachment.circuit_breaker_recovery_basic,
  ]
}

resource "aws_cloudwatch_log_group" "circuit_breaker_recovery" {
  name              = "/aws/lambda/${local.resource_prefix}CircuitBreakerRecovery"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}CircuitBreakerRecoveryLogs"
  })
}

data "archive_file" "drift_recovery" {
  type        = "zip"
  source_file = "${path.module}/lambdas/drift_recovery.py"
  output_path = "${path.module}/.terraform/lambda_packages/drift_recovery.zip"
}

resource "aws_lambda_function" "drift_recovery" {
  filename         = data.archive_file.drift_recovery.output_path
  function_name    = "${local.resource_prefix}DriftRecovery"
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
    Name = "${local.resource_prefix}DriftRecovery"
  })

  depends_on = [
    aws_iam_role_policy.drift_recovery_permissions,
    aws_iam_role_policy_attachment.drift_recovery_basic,
  ]
}

resource "aws_cloudwatch_log_group" "drift_recovery" {
  name              = "/aws/lambda/${local.resource_prefix}DriftRecovery"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}DriftRecoveryLogs"
  })
}

resource "aws_lambda_event_source_mapping" "drift_recovery_sqs" {
  event_source_arn = aws_sqs_queue.drift_recovery.arn
  function_name    = aws_lambda_function.drift_recovery.arn
  batch_size       = 1
}

data "archive_file" "spot_interruption_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/spot_interruption_handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/spot_interruption_handler.zip"
}

resource "aws_lambda_function" "spot_interruption_handler" {
  filename         = data.archive_file.spot_interruption_handler.output_path
  function_name    = "${local.resource_prefix}SpotInterruptionHandler"
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
    Name = "${local.resource_prefix}SpotInterruptionHandler"
  })

  depends_on = [
    aws_iam_role_policy.spot_interruption_handler_permissions,
    aws_iam_role_policy_attachment.spot_interruption_handler_basic,
  ]
}

resource "aws_cloudwatch_log_group" "spot_interruption_handler" {
  name              = "/aws/lambda/${local.resource_prefix}SpotInterruptionHandler"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}SpotInterruptionHandlerLogs"
  })
}

data "archive_file" "stale_runner_cleanup" {
  type        = "zip"
  source_file = "${path.module}/lambdas/stale_runner_cleanup.py"
  output_path = "${path.module}/.terraform/lambda_packages/stale_runner_cleanup.zip"
}

resource "aws_lambda_function" "stale_runner_cleanup" {
  filename         = data.archive_file.stale_runner_cleanup.output_path
  function_name    = "${local.resource_prefix}StaleRunnerCleanup"
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
      WORKFLOW_RUNNERS_TABLE   = aws_dynamodb_table.workflow_runners.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.stale_runner_cleanup.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}StaleRunnerCleanup"
  })

  depends_on = [
    aws_iam_role_policy.stale_runner_cleanup_permissions,
    aws_iam_role_policy_attachment.stale_runner_cleanup_basic,
  ]
}

resource "aws_cloudwatch_log_group" "stale_runner_cleanup" {
  name              = "/aws/lambda/${local.resource_prefix}StaleRunnerCleanup"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}StaleRunnerCleanupLogs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.runners_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}
