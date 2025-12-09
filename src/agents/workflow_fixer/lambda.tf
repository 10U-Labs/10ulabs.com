# Webhook Lambda - receives GitHub webhook and invokes AgentCore agent
# Package Lambda with dependencies
resource "null_resource" "webhook_lambda_deps" {
  triggers = {
    requirements = filemd5("${path.module}/webhook_lambda/requirements.txt")
    handler      = filemd5("${path.module}/webhook_lambda/handler.py")
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${path.module}/.terraform/lambda_build
      mkdir -p ${path.module}/.terraform/lambda_build
      pip install -r ${path.module}/webhook_lambda/requirements.txt \
        -t ${path.module}/.terraform/lambda_build \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        --quiet
      cp ${path.module}/webhook_lambda/handler.py ${path.module}/.terraform/lambda_build/
    EOT
  }
}

data "archive_file" "webhook_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/.terraform/lambda_build"
  output_path = "${path.module}/.terraform/lambda_packages/webhook.zip"
  depends_on  = [null_resource.webhook_lambda_deps]
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
  description      = "Webhook handler for Workflow Fixer Agent"

  environment {
    variables = {
      AGENT_RUNTIME_ARN          = aws_bedrockagentcore_agent_runtime.workflow_fixer.agent_runtime_arn
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
