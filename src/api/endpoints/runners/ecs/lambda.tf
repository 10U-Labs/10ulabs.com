resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.lambda.output_path
  function_name    = local.lambda_function_name
  handler          = local.lambda_handler
  role             = aws_iam_role.lambda_execution.arn
  runtime          = local.lambda_runtime
  architectures    = ["arm64"]
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size

  environment {
    variables = {
      CONTAINER_NAME           = var.container_name
      ECR_REPOSITORY           = data.terraform_remote_state.api_shared_docker_repository.outputs.ecr_repository_name
      ECS_CLUSTER              = aws_ecs_cluster.runner.name
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.runners.outputs.github_token_secret_name
      IMAGE_API_ENDPOINT       = data.terraform_remote_state.runners.outputs.api_endpoint
      SECURITY_GROUPS          = data.terraform_remote_state.api_shared_networking.outputs.security_group_id_for_runners
      SUBNETS                  = data.terraform_remote_state.api_shared_networking.outputs.public_subnet_ids
      TASK_DEFINITION          = aws_ecs_task_definition.runner.arn
      USE_SPOT                 = tostring(module.shared.runners_config.fargate.use_spot)
      VPC_ID                   = data.terraform_remote_state.api_shared_networking.outputs.vpc_id
      WORKFLOW_RUNNERS_TABLE   = data.terraform_remote_state.runners.outputs.workflow_runners_table_name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda_execution.id]
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 14
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}

# SQS event source mapping for requests from /v1/runners endpoint
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn                   = aws_sqs_queue.main.arn
  function_name                      = aws_lambda_function.handler.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}
