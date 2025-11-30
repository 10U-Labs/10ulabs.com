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

