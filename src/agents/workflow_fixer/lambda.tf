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
      AGENT_RUNTIME_ARN = aws_bedrockagentcore_agent_runtime.workflow_fixer.arn
      SSM_GITHUB_PAT    = local.ssm_github_pat
      AWS_REGION_NAME   = local.aws_region
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
