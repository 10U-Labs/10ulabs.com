data "archive_file" "handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  source {
    content  = file("${path.module}/../../../../etc/runners.json")
    filename = "etc/runners.json"
  }
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.handler.output_path
  function_name    = local.lambda_function_name
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_mb
  description      = "Router for /v1/runners - routes requests to EC2 or ECS runners"

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
    log_group  = aws_cloudwatch_log_group.handler.name
  }

  tags = merge(local.common_tags, {
    Name = local.lambda_function_name
  })

  depends_on = [
    aws_iam_role_policy.sqs_access,
    aws_iam_role_policy.ssm_access,
    aws_iam_role_policy.kms_access,
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_xray,
  ]

  # Force Lambda replacement when IAM role is recreated
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = local.lambda_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.lambda_function_name}Logs"
  })
}

# Event source mapping for SQS queue
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn                   = aws_sqs_queue.main.arn
  function_name                      = aws_lambda_function.handler.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}

# Allow API Gateway to invoke Lambda (for direct invocation if needed)
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}
