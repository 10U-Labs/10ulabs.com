data "archive_file" "health_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/health.py"
  output_path = "${path.module}/.terraform/lambda_packages/health_handler.zip"
}

resource "aws_lambda_function" "health_handler" {
  filename         = data.archive_file.health_handler.output_path
  function_name    = "HealthHandler"
  role             = aws_iam_role.lambda_health_handler.arn
  handler          = "health.handler"
  source_code_hash = data.archive_file.health_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  description      = "Health check endpoint for API"

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.health_handler.name
  }

  tags = {
    Name = "HealthHandler"
  }
}

resource "aws_cloudwatch_log_group" "health_handler" {
  name              = "/aws/lambda/HealthHandler"
  retention_in_days = 7

  tags = {
    Name = "HealthHandler-logs"
  }
}

data "archive_file" "catchall_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/catchall.py"
  output_path = "${path.module}/.terraform/lambda_packages/catchall_handler.zip"
}

resource "aws_lambda_function" "catchall_handler" {
  filename         = data.archive_file.catchall_handler.output_path
  function_name    = "CatchAllHandler"
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

  tags = {
    Name = "CatchAllHandler"
  }
}

resource "aws_cloudwatch_log_group" "catchall_handler" {
  name              = "/aws/lambda/CatchAllHandler"
  retention_in_days = 7

  tags = {
    Name = "CatchAllHandler-logs"
  }
}

data "archive_file" "runners_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/webhook_router.py"
  output_path = "${path.module}/.terraform/lambda_packages/runners_handler.zip"
}

resource "aws_lambda_function" "runners_handler" {
  filename         = data.archive_file.runners_handler.output_path
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_runners_handler.arn
  handler          = "webhook_router.lambda_handler"
  source_code_hash = data.archive_file.runners_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = var.lambda_timeout_seconds
  memory_size      = var.lambda_memory_mb
  description      = "GitHub webhook router for GitHub self-hosted runners"

  environment {
    variables = {
      WEBHOOK_SECRET_NAME    = aws_ssm_parameter.webhook_secret.name
      API_BASE_URL           = "https://${var.domain_subdomain}"
      IDEMPOTENCY_TABLE_NAME = aws_dynamodb_table.idempotency.name
      JOB_QUEUE_URL          = aws_sqs_queue.job_queue.url
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

  tags = {
    Name = var.lambda_function_name
  }
}

resource "aws_cloudwatch_log_group" "runners_handler" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.lambda_function_name}-logs"
  }
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
  function_name    = "V1ApiHandler"
  role             = aws_iam_role.lambda_v1_handler.arn
  handler          = "v1.lambda_handler"
  source_code_hash = data.archive_file.v1_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = var.lambda_timeout_seconds
  memory_size      = var.lambda_memory_mb
  description      = "Unified Lambda handler for all /v1/* API endpoints"

  environment {
    variables = {
      SUBNETS                  = join(",", aws_subnet.public[*].id)
      SECURITY_GROUPS          = aws_security_group.runner_sg.id
      VPC_ID                   = aws_vpc.runner_vpc.id
      ECS_CLUSTER              = aws_ecs_cluster.runner.arn
      TASK_DEFINITION          = aws_ecs_task_definition.runner.arn
      CONTAINER_NAME           = var.container_name
      EC2_INSTANCE_TYPES       = join(",", var.ec2_spot_instance_types)
      EC2_IAM_INSTANCE_PROFILE = aws_iam_instance_profile.ec2_runner.name
      EC2_MAX_PRICE            = var.ec2_max_spot_price
      GITHUB_TOKEN_SECRET_NAME = var.github_token_secret_name
      GITHUB_REPO              = var.github_repo
      ECR_REPOSITORY           = aws_ecr_repository.runner.name
      IMAGE_API_ENDPOINT       = "https://${var.domain_subdomain}"
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.v1_handler.name
  }

  tags = {
    Name = "V1ApiHandler"
  }
}

resource "aws_cloudwatch_log_group" "v1_handler" {
  name              = "/aws/lambda/V1ApiHandler"
  retention_in_days = 7

  tags = {
    Name = "V1ApiHandler-logs"
  }
}
