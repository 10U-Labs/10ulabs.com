# Webhook Lambda - Routes requests to AgentCore runtime
#
# This Lambda handles:
# 1. GitHub webhook events (workflow failures)
# 2. Scheduled scans for unresolved failures
# 3. Orchestration (routing between agents based on recommendations)

data "archive_file" "webhook_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambdas/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/webhook.zip"
}

resource "aws_lambda_function" "webhook" {
  filename         = data.archive_file.webhook_lambda.output_path
  function_name    = local.lambda_name
  role             = aws_iam_role.webhook_lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.webhook_lambda.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 300
  memory_size      = 256
  description      = "Agent webhook handler - routes requests to AgentCore"
  layers           = [aws_lambda_layer_version.github_auth.arn]

  environment {
    variables = {
      AGENT_RUNTIME_ARN          = aws_bedrockagentcore_agent_runtime.runtime.agent_runtime_arn
      AWS_REGION_NAME            = local.aws_region
      GITHUB_ORG                 = module.shared.github_org
      GITHUB_REPO                = module.shared.name_for_github_repo
      SSM_GITHUB_APP_ID          = local.github_app_ssm.id
      SSM_GITHUB_APP_INSTALL_ID  = local.github_app_ssm.installation_id
      SSM_GITHUB_APP_PRIVATE_KEY = local.github_app_ssm.private_key
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.webhook_lambda.name
  }

  tags = merge(local.common_tags, {
    Name = local.lambda_name
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.webhook_lambda.id]
  }
}

resource "aws_cloudwatch_log_group" "webhook_lambda" {
  name              = local.log_group_name
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}Logs"
  })
}

# Lambda Function URL for GitHub webhook
resource "aws_lambda_function_url" "webhook" {
  function_name      = aws_lambda_function.webhook.function_name
  authorization_type = "NONE"
}

# Allow public access to Function URL
resource "aws_lambda_permission" "function_url" {
  statement_id           = "FunctionURLAllowPublicAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.webhook.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

# EventBridge rule for scheduled scans
resource "aws_cloudwatch_event_rule" "scheduled_scan" {
  name                = "${local.lambda_name}-scheduled-scan"
  description         = "Trigger agent to scan for unresolved workflow failures"
  schedule_expression = "rate(15 minutes)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "scheduled_scan" {
  rule      = aws_cloudwatch_event_rule.scheduled_scan.name
  target_id = "AgentWebhookLambda"
  arn       = aws_lambda_function.webhook.arn
}

resource "aws_lambda_permission" "scheduled_scan" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_scan.arn
}
