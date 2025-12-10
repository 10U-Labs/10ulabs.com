data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.handler.output_path
  function_name    = "${local.resource_prefix}-RackDesignerHandler"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128
  description      = "Rack Designer API handler for saving and loading configurations"

  environment {
    variables = {
      RACK_DESIGNER_CONFIGURATIONS_TABLE = aws_dynamodb_table.configurations.name
      RACK_DESIGNER_EVENTS_TABLE         = aws_dynamodb_table.events.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.handler.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-RackDesignerHandler"
  })
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = "/aws/lambda/${local.resource_prefix}-RackDesignerHandler"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}RackDesignerHandlerLogs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}
