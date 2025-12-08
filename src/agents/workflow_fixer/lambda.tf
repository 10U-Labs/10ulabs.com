# Webhook Lambda - receives GitHub webhook and invokes AgentCore agent
data "archive_file" "webhook_lambda" {
  type        = "zip"
  source_file = "${path.module}/webhook-lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/webhook.zip"
}

resource "aws_lambda_function" "webhook" {
  filename         = data.archive_file.webhook_lambda.output_path
  function_name    = local.lambda_name
  role             = aws_iam_role.webhook_lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.webhook_lambda.output_base64sha256
  runtime          = "python3.13"
  timeout          = 300
  memory_size      = 256
  description      = "Webhook handler for Workflow Fixer Agent"

  environment {
    variables = {
      AGENT_RUNTIME_ARN = aws_bedrockagentcore_agent_runtime.workflow_fixer.agent_runtime_arn
      SSM_GITHUB_PAT    = local.ssm_github_pat
      AWS_REGION_NAME   = local.aws_region
      GITHUB_ORG        = "10U-Labs-LLC"
      GITHUB_REPO       = "10ulabs.com"
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
  description         = "Trigger workflow fixer to scan for unresolved failures"
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
