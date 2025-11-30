data "archive_file" "echo_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/echo_handler.zip"
}

resource "aws_lambda_function" "echo_handler" {
  filename         = data.archive_file.echo_handler.output_path
  function_name    = var.echo_handler_function_name
  role             = aws_iam_role.lambda_echo_handler.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.echo_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  description      = "Echo endpoint for API"

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.echo_handler.name
  }

  tags = merge(local.common_tags, {
    Name = var.echo_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "echo_handler" {
  name              = var.echo_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.echo_handler_function_name}-logs"
  })
}
