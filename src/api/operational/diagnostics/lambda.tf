data "archive_file" "diagnostics_handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/../../../../lib/python/lambda_http/__init__.py")
    filename = "lambda_http.py"
  }
  output_path = "${path.module}/.terraform/lambda_packages/diagnostics_handler.zip"
}

resource "aws_lambda_function" "diagnostics_handler" {
  filename         = data.archive_file.diagnostics_handler.output_path
  function_name    = var.diagnostics_handler_function_name
  role             = aws_iam_role.lambda_diagnostics_handler.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.diagnostics_handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  description      = "Diagnostics endpoint for API"

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.diagnostics_handler.name
  }

  tags = merge(local.common_tags, {
    Name = var.diagnostics_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "diagnostics_handler" {
  name              = var.diagnostics_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.diagnostics_handler_function_name}Logs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.diagnostics_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_id}/*"
}
