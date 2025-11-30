data "archive_file" "catchall_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/catchall.py"
  output_path = "${path.module}/.terraform/lambda_packages/catchall_handler.zip"
}

resource "aws_lambda_function" "catchall_handler" {
  filename         = data.archive_file.catchall_handler.output_path
  function_name    = var.catchall_handler_function_name
  role             = aws_iam_role.lambda_catchall_handler.arn
  handler          = "catchall.handler"
  source_code_hash = data.archive_file.catchall_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  description      = "Catch-all handler for undefined routes"


  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.catchall_handler.name
  }

  tags = merge(local.common_tags, {
    Name = var.catchall_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "catchall_handler" {
  name              = var.catchall_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.catchall_handler_function_name}-logs"
  })
}

data "archive_file" "runners_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/webhook_router.py"
  output_path = "${path.module}/.terraform/lambda_packages/runners_handler.zip"
}

resource "aws_lambda_function" "runners_handler" {
  filename                       = data.archive_file.runners_handler.output_path
  function_name                  = var.lambda_function_name
  role                           = aws_iam_role.lambda_runners_handler.arn
  handler                        = "webhook_router.lambda_handler"
  source_code_hash               = data.archive_file.runners_handler.output_base64sha256
  runtime                        = "python3.13"
  timeout                        = var.lambda_timeout_seconds
  memory_size                    = var.lambda_memory_mb
  reserved_concurrent_executions = -1
  description                    = "GitHub webhook router for GitHub self-hosted runners"


  environment {
    variables = {
      WEBHOOK_SECRET_NAME           = aws_ssm_parameter.webhook_secret.name
      API_KEY_PARAMETER_NAME        = aws_ssm_parameter.api_key.name
      API_BASE_URL                  = "https://${local.api_fqdn}"
      IDEMPOTENCY_TABLE_NAME        = aws_dynamodb_table.idempotency.name
      JOB_QUEUE_URL                 = aws_sqs_queue.job_queue.url
      RUNNER_LABEL_EC2_SPOT         = local.runner_label_ec2_spot
      RUNNER_LABEL_EC2_SPOT_E2E     = local.runner_label_ec2_spot_e2e
      RUNNER_LABEL_FARGATE_SPOT     = local.runner_label_fargate_spot
      RUNNER_LABEL_FARGATE_SPOT_E2E = local.runner_label_fargate_spot_e2e
      WORKFLOW_RUNNERS_TABLE        = aws_dynamodb_table.workflow_runners.name
      GITHUB_TOKEN_SECRET_NAME      = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
      ECS_CLUSTER                   = aws_ecs_cluster.runner.arn
      GITHUB_REPO                   = local.github_repo_full
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
    Name = var.lambda_function_name
  })
}

resource "aws_cloudwatch_log_group" "runners_handler" {
  name              = var.webhook_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.lambda_function_name}-logs"
  })
}

resource "aws_lambda_event_source_mapping" "runners_handler_sqs" {
  event_source_arn                   = aws_sqs_queue.job_queue.arn
  function_name                      = aws_lambda_function.runners_handler.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}

data "archive_file" "v1_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/v1.py"
  output_path = "${path.module}/.terraform/lambda_packages/v1_handler.zip"
}

resource "aws_lambda_function" "v1_handler" {
  filename         = data.archive_file.v1_handler.output_path
  function_name    = var.v1_handler_function_name
  role             = aws_iam_role.lambda_v1_handler.arn
  handler          = "v1.lambda_handler"
  source_code_hash = data.archive_file.v1_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = var.lambda_timeout_seconds
  memory_size      = var.lambda_memory_mb
  description      = "Unified Lambda handler for all /v1/* API endpoints"


  environment {
    variables = {
      API_DOMAIN               = local.api_fqdn
      API_KEY_PARAMETER_NAME   = aws_ssm_parameter.api_key.name
      CONTAINER_NAME           = var.container_name
      EC2_AMI_PURPOSE_TAG      = local.ec2_runner_ami_purpose_tag
      EC2_AMI_PURPOSE_VALUE    = local.ec2_runner_ami_purpose_value
      EC2_AMI_STABLE_TAG       = local.ec2_runner_ami_stable_tag
      EC2_MANAGED_BY_TAG       = local.ec2_runner_managed_by_tag
      EC2_IAM_INSTANCE_PROFILE = aws_iam_instance_profile.ec2_runner.name
      EC2_INSTANCE_TYPES       = join(",", var.ec2_spot_instance_types)
      EC2_MAX_PRICE            = var.ec2_max_spot_price
      ECR_REPOSITORY           = data.terraform_remote_state.ecr.outputs.repository_name
      ECS_CLUSTER              = aws_ecs_cluster.runner.arn
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
      IMAGE_API_ENDPOINT       = "https://${local.api_fqdn}"
      SECURITY_GROUPS          = aws_security_group.runner_sg.id
      SUBNETS                  = join(",", aws_subnet.public[*].id)
      TASK_DEFINITION          = aws_ecs_task_definition.runner.arn
      VPC_ID                   = aws_vpc.runner_vpc.id
      WORKFLOW_RUNNERS_TABLE   = aws_dynamodb_table.workflow_runners.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.v1_handler.name
  }

  tags = merge(local.common_tags, {
    Name = var.v1_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "v1_handler" {
  name              = var.v1_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.v1_handler_function_name}-logs"
  })
}

data "archive_file" "circuit_breaker_remediation" {
  type        = "zip"
  source_file = "${path.module}/lambdas/circuit_breaker_remediation.py"
  output_path = "${path.module}/.terraform/lambda_packages/circuit_breaker_remediation.zip"
}

resource "aws_lambda_function" "circuit_breaker_remediation" {
  filename         = data.archive_file.circuit_breaker_remediation.output_path
  function_name    = "${local.resource_prefix}-CircuitBreakerRemediation"
  role             = aws_iam_role.circuit_breaker_remediation.arn
  handler          = "circuit_breaker_remediation.lambda_handler"
  source_code_hash = data.archive_file.circuit_breaker_remediation.output_base64sha256
  runtime          = "python3.13"
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
    Name = "${local.resource_prefix}-CircuitBreakerRemediation"
  })
}

resource "aws_cloudwatch_log_group" "circuit_breaker_remediation" {
  name              = "/aws/lambda/${local.resource_prefix}-CircuitBreakerRemediation"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-CircuitBreakerRemediation-logs"
  })
}

data "archive_file" "dlq_reprocessor" {
  type        = "zip"
  source_file = "${path.module}/lambdas/dlq_reprocessor.py"
  output_path = "${path.module}/.terraform/lambda_packages/dlq_reprocessor.zip"
}

resource "aws_lambda_function" "dlq_reprocessor" {
  filename         = data.archive_file.dlq_reprocessor.output_path
  function_name    = "${local.resource_prefix}-DLQReprocessor"
  role             = aws_iam_role.dlq_reprocessor.arn
  handler          = "dlq_reprocessor.handler"
  source_code_hash = data.archive_file.dlq_reprocessor.output_base64sha256
  runtime          = "python3.13"
  timeout          = 300
  memory_size      = 256
  description      = "Reprocesses messages from DLQs"


  environment {
    variables = {
      WEBHOOK_DLQ_URL             = aws_sqs_queue.webhook_dlq.url
      JOB_DLQ_URL                 = aws_sqs_queue.job_queue_dlq.url
      JOB_QUEUE_URL               = aws_sqs_queue.job_queue.url
      SNS_TOPIC_ARN               = aws_sns_topic.circuit_breaker_alerts.arn
      GITHUB_TOKEN_PARAMETER_NAME = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.dlq_reprocessor.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-DLQReprocessor"
  })
}

resource "aws_cloudwatch_log_group" "dlq_reprocessor" {
  name              = "/aws/lambda/${local.resource_prefix}-DLQReprocessor"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-DLQReprocessor-logs"
  })
}

data "archive_file" "circuit_breaker_recovery" {
  type        = "zip"
  source_file = "${path.module}/lambdas/circuit_breaker_recovery.py"
  output_path = "${path.module}/.terraform/lambda_packages/circuit_breaker_recovery.zip"
}

resource "aws_lambda_function" "circuit_breaker_recovery" {
  filename         = data.archive_file.circuit_breaker_recovery.output_path
  function_name    = "${local.resource_prefix}-CircuitBreakerRecovery"
  role             = aws_iam_role.circuit_breaker_recovery.arn
  handler          = "circuit_breaker_recovery.lambda_handler"
  source_code_hash = data.archive_file.circuit_breaker_recovery.output_base64sha256
  runtime          = "python3.13"
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
    Name = "${local.resource_prefix}-CircuitBreakerRecovery"
  })
}

resource "aws_cloudwatch_log_group" "circuit_breaker_recovery" {
  name              = "/aws/lambda/${local.resource_prefix}-CircuitBreakerRecovery"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-CircuitBreakerRecovery-logs"
  })
}

data "archive_file" "drift_recovery" {
  type        = "zip"
  source_file = "${path.module}/lambdas/drift_recovery.py"
  output_path = "${path.module}/.terraform/lambda_packages/drift_recovery.zip"
}

resource "aws_lambda_function" "drift_recovery" {
  filename         = data.archive_file.drift_recovery.output_path
  function_name    = "${local.resource_prefix}-DriftRecovery"
  role             = aws_iam_role.drift_recovery.arn
  handler          = "drift_recovery.lambda_handler"
  source_code_hash = data.archive_file.drift_recovery.output_base64sha256
  runtime          = "python3.13"
  timeout          = 30
  memory_size      = 256
  description      = "Triggers API workflow when infrastructure drift is detected"


  environment {
    variables = {
      GITHUB_REPO                 = local.github_repo_full
      GITHUB_TOKEN_PARAMETER_NAME = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
      SNS_TOPIC_ARN               = aws_sns_topic.circuit_breaker_alerts.arn
      MANAGED_VPC_ID              = aws_vpc.runner_vpc.id
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.drift_recovery.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-DriftRecovery"
  })
}

resource "aws_cloudwatch_log_group" "drift_recovery" {
  name              = "/aws/lambda/${local.resource_prefix}-DriftRecovery"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-DriftRecovery-logs"
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
  function_name    = "${local.resource_prefix}-SpotInterruptionHandler"
  role             = aws_iam_role.spot_interruption_handler.arn
  handler          = "spot_interruption_handler.lambda_handler"
  source_code_hash = data.archive_file.spot_interruption_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 60
  memory_size      = 256
  description      = "Handles spot interruption events and launches replacement runners"


  environment {
    variables = {
      API_BASE_URL             = "https://${local.api_fqdn}"
      API_KEY                  = random_password.api_key.result
      ECS_CLUSTER              = aws_ecs_cluster.runner.arn
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
      WORKFLOW_RUNNERS_TABLE   = aws_dynamodb_table.workflow_runners.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.spot_interruption_handler.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-SpotInterruptionHandler"
  })
}

resource "aws_cloudwatch_log_group" "spot_interruption_handler" {
  name              = "/aws/lambda/${local.resource_prefix}-SpotInterruptionHandler"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-SpotInterruptionHandler-logs"
  })
}

resource "aws_cloudwatch_event_rule" "ecs_task_stopped" {
  name        = "${local.resource_prefix}-ECSTaskStopped"
  description = "Triggers on ECS task stopped events for spot interruption handling"

  event_pattern = jsonencode({
    source      = ["aws.ecs"]
    detail-type = ["ECS Task State Change"]
    detail = {
      clusterArn = [aws_ecs_cluster.runner.arn]
      lastStatus = ["STOPPED"]
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-ECSTaskStopped"
  })
}

resource "aws_cloudwatch_event_target" "ecs_task_stopped" {
  rule      = aws_cloudwatch_event_rule.ecs_task_stopped.name
  target_id = "SpotInterruptionHandler"
  arn       = aws_lambda_function.spot_interruption_handler.arn
}

resource "aws_lambda_permission" "ecs_task_stopped" {
  statement_id  = "AllowECSTaskStoppedEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spot_interruption_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ecs_task_stopped.arn
}

resource "aws_cloudwatch_event_rule" "ec2_spot_interruption" {
  name        = "${local.resource_prefix}-EC2SpotInterruption"
  description = "Triggers on EC2 spot interruption warnings"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Spot Instance Interruption Warning"]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-EC2SpotInterruption"
  })
}

resource "aws_cloudwatch_event_target" "ec2_spot_interruption" {
  rule      = aws_cloudwatch_event_rule.ec2_spot_interruption.name
  target_id = "SpotInterruptionHandler"
  arn       = aws_lambda_function.spot_interruption_handler.arn
}

resource "aws_lambda_permission" "ec2_spot_interruption" {
  statement_id  = "AllowEC2SpotInterruptionEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spot_interruption_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_spot_interruption.arn
}

data "archive_file" "stale_runner_cleanup" {
  type        = "zip"
  source_file = "${path.module}/lambdas/stale_runner_cleanup.py"
  output_path = "${path.module}/.terraform/lambda_packages/stale_runner_cleanup.zip"
}

resource "aws_lambda_function" "stale_runner_cleanup" {
  filename         = data.archive_file.stale_runner_cleanup.output_path
  function_name    = "${local.resource_prefix}-StaleRunnerCleanup"
  role             = aws_iam_role.stale_runner_cleanup.arn
  handler          = "stale_runner_cleanup.lambda_handler"
  source_code_hash = data.archive_file.stale_runner_cleanup.output_base64sha256
  runtime          = "python3.13"
  timeout          = 300
  memory_size      = 256
  description      = "Cleans up stale runners from completed or failed workflows"


  environment {
    variables = {
      ECS_CLUSTER              = aws_ecs_cluster.runner.arn
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
      WORKFLOW_RUNNERS_TABLE   = aws_dynamodb_table.workflow_runners.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.stale_runner_cleanup.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-StaleRunnerCleanup"
  })
}

resource "aws_cloudwatch_log_group" "stale_runner_cleanup" {
  name              = "/aws/lambda/${local.resource_prefix}-StaleRunnerCleanup"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-StaleRunnerCleanup-logs"
  })
}

resource "aws_cloudwatch_event_rule" "stale_runner_cleanup_schedule" {
  name                = "${local.resource_prefix}-StaleRunnerCleanupSchedule"
  description         = "Triggers stale runner cleanup every 15 minutes"
  schedule_expression = "rate(15 minutes)"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-StaleRunnerCleanupSchedule"
  })
}

resource "aws_cloudwatch_event_target" "stale_runner_cleanup" {
  rule      = aws_cloudwatch_event_rule.stale_runner_cleanup_schedule.name
  target_id = "StaleRunnerCleanup"
  arn       = aws_lambda_function.stale_runner_cleanup.arn
}

resource "aws_lambda_permission" "stale_runner_cleanup" {
  statement_id  = "AllowScheduledEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stale_runner_cleanup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stale_runner_cleanup_schedule.arn
}
