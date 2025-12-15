data "archive_file" "action_group" {
  type        = "zip"
  source_file = "${path.module}/lambdas/action_group.py"
  output_path = "${path.module}/.terraform/lambda_packages/action_group.zip"
}

resource "aws_lambda_function" "action_group" {
  filename         = data.archive_file.action_group.output_path
  function_name    = local.lambda_name
  role             = aws_iam_role.lambda_action_group.arn
  handler          = "action_group.handler"
  source_code_hash = data.archive_file.action_group.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 300
  memory_size      = 512
  description      = "Action group for Test Auditor Agent - GitHub operations"
  layers           = [data.terraform_remote_state.agents_shared.outputs.lambda_layer_github_auth_arn]

  environment {
    variables = {
      GITHUB_ORG                 = local.github_org
      GITHUB_REPO                = local.github_repo
      SSM_GITHUB_APP_ID          = local.github_app_ssm.id
      SSM_GITHUB_APP_INSTALL_ID  = local.github_app_ssm.installation_id
      SSM_GITHUB_APP_PRIVATE_KEY = local.github_app_ssm.private_key
      DOCS_APPROACH              = "docs/APPROACH_TO_PRE_DEPLOYMENT_INTEGRATION_TESTS.md"
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.action_group.name
  }

  tags = merge(local.common_tags, {
    Name = local.lambda_name
  })

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda_action_group.id]
  }
}

resource "aws_cloudwatch_log_group" "action_group" {
  name              = local.log_group_name
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}Logs"
  })
}
