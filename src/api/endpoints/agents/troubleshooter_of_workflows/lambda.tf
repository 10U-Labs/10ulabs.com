# Webhook Lambda - receives GitHub webhook and invokes AgentCore agent
# Dependencies (PyJWT, cryptography) come from the shared github_auth layer in bootstrap

data "archive_file" "webhook_lambda" {
  type        = "zip"
  source_file = "${path.module}/webhook_lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/webhook.zip"
}

resource "aws_lambda_function" "webhook" {
  filename         = data.archive_file.webhook_lambda.output_path
  function_name    = local.lambda_name
  role             = aws_iam_role.webhook_lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.webhook_lambda.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["x86_64"]
  timeout          = 300
  memory_size      = 256
  description      = "Webhook handler for Troubleshooter of Workflows Agent"
  layers           = [data.terraform_remote_state.agents_shared.outputs.lambda_layer_github_auth_arn]

  environment {
    variables = {
      AGENT_RUNTIME_ARN          = aws_bedrockagentcore_agent_runtime.troubleshooter_of_workflows.agent_runtime_arn
      AWS_REGION_NAME            = local.aws_region
      GITHUB_ORG                 = "10U-Labs-LLC"
      GITHUB_REPO                = "10ulabs.com"
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
}

resource "aws_cloudwatch_log_group" "webhook_lambda" {
  name              = local.log_group_name
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}-logs"
  })
}

# Lambda Function URL for GitHub webhook
resource "aws_lambda_function_url" "webhook" {
  function_name      = aws_lambda_function.webhook.function_name
  authorization_type = "NONE"
}

# EventBridge rule to scan for unresolved failures every 15 minutes
resource "aws_cloudwatch_event_rule" "scheduled_scan" {
  name                = "${local.lambda_name}-scheduled-scan"
  description         = "Trigger troubleshooter of workflows to scan for unresolved failures"
  schedule_expression = "rate(15 minutes)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "scheduled_scan" {
  rule      = aws_cloudwatch_event_rule.scheduled_scan.name
  target_id = "WorkflowFixerLambda"
  arn       = aws_lambda_function.webhook.arn
}

resource "aws_lambda_permission" "scheduled_scan" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_scan.arn
}
