data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.handler.output_path
  function_name    = "${local.resource_prefix}-ImageForDockerRunnersHandler"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  description      = "Handler for /v1/image-for-docker-runners API endpoints"

  environment {
    variables = {
      ECR_REPOSITORY           = local.ecr_repository_name
      GITHUB_REPO              = local.github_repo_full
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.handler.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-ImageForDockerRunnersHandler"
  })
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = "/aws/lambda/${local.resource_prefix}-ImageForDockerRunnersHandler"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-ImageForDockerRunnersHandler-logs"
  })
}

