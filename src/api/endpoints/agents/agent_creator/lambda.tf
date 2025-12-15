data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/webhook_lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "invoke" {
  filename         = data.archive_file.lambda.output_path
  function_name    = local.lambda_name
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 300
  memory_size      = 256
  description      = "Invocation handler for Agent Creator"
  layers           = [data.terraform_remote_state.agents_shared.outputs.lambda_layer_github_auth_arn]

  environment {
    variables = {
      AGENT_RUNTIME_ARN          = aws_bedrockagentcore_agent_runtime.agent_creator.arn
      AWS_REGION_NAME            = local.aws_region
      SSM_GITHUB_APP_ID          = local.github_app_ssm.id
      SSM_GITHUB_APP_INSTALL_ID  = local.github_app_ssm.installation_id
      SSM_GITHUB_APP_PRIVATE_KEY = local.github_app_ssm.private_key
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.lambda.name
  }

  tags = merge(local.common_tags, {
    Name = local.lambda_name
  })

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = local.log_group_name
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}Logs"
  })
}

resource "aws_lambda_function_url" "invoke" {
  function_name      = aws_lambda_function.invoke.function_name
  authorization_type = "NONE"
}

# Allow public access to Function URL
resource "aws_lambda_permission" "function_url" {
  statement_id           = "FunctionURLAllowPublicAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.invoke.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}
