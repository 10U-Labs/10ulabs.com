data "archive_file" "health_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/health_handler.zip"
}

resource "aws_lambda_function" "health_handler" {
  filename         = data.archive_file.health_handler.output_path
  function_name    = var.health_handler_function_name
  role             = aws_iam_role.lambda_health_handler.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.health_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  description      = "Health check endpoint for API"

  environment {
    variables = {
      SECURITY_GROUPS = data.terraform_remote_state.api.outputs.runner_security_group_id
      SUBNETS         = data.terraform_remote_state.api.outputs.vpc_public_subnet_ids
      VPC_ID          = data.terraform_remote_state.api.outputs.vpc_id
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.health_handler.name
  }

  tags = merge(local.common_tags, {
    Name = var.health_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "health_handler" {
  name              = var.health_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.health_handler_function_name}-logs"
  })
}

