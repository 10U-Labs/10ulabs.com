data "archive_file" "health_handler" {
  type        = "zip"
  source_file = "${path.module}/health.py"
  output_path = "${path.module}/.terraform/lambda_packages/health_handler.zip"
}

resource "aws_lambda_function" "health_handler" {
  filename         = data.archive_file.health_handler.output_path
  function_name    = var.health_handler_function_name
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

  tags = merge(local.common_tags, {
    Name = var.health_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "health_handler" {
  name              = var.health_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.health_handler_function_name}-logs"
  })
}

resource "aws_cloudwatch_log_subscription_filter" "health_handler" {
  name            = "health-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.health_handler.name
  filter_pattern  = ""
  destination_arn = data.terraform_remote_state.api.outputs.firehose_delivery_stream_arn
  role_arn        = data.terraform_remote_state.api.outputs.cloudwatch_logs_firehose_role_arn
}

resource "aws_lambda_permission" "health_handler" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${data.terraform_remote_state.api.outputs.api_gateway_execution_arn}/*/GET/health"
}
